# Mobile Security, Cryptography & Zero-Trust Engine

> Reference status: client architecture study material. Embedded code and payloads are incomplete design sketches, not verified production implementations or records from the named products. Do not quote remaining numeric tuning choices as employer benchmarks. For backend preparation, start with the [backend guide](backend-engineering-manager-guide.md) and [evidence standard](evidence-and-sources.md).


## Overview
For Staff, Principal, and Engineering Manager roles across fintech (Stripe, Square, PayPal), ride-sharing (Uber, Lyft), and privacy-first platforms (Apple, Signal, Meta), **Mobile Security Architecture & Cryptography** is a critical system design topic. This specification covers client-side Zero-Trust security, hardware-backed key management (Secure Enclave / SEP), App Attestation (Apple DeviceCheck / App Attest), Certificate Pinning (SPKI), local storage encryption (SQLCipher encryption with its documented authentication design), and anti-tamper runtime protection.

## Scope Definition

### In Scope
- Device Integrity & Hardware Attestation (Apple DeviceCheck / DCAppAttestService).
- Hardware-backed Cryptographic Key Derivation (Secure Enclave, `SecAccessControl`, `SecKeyGeneratePair`).
- Public Key Pinning (Subject Public Key Info / SPKI Pinning with TLS 1.3).
- Encrypted Local Storage (SQLCipher database encryption + Keychain key protection).
- Anti-Tamper & Anti-Jailbreak Runtime Detection (Dyld insertion checks, debugger attachment check).

### Out of Scope
- Server-side Hardware Security Modules (HSM) architecture.
- Web-based OAuth2 redirection security (covered in `docs/authentication-oauth-biometric.md`).
- PCI-DSS server compliance certification auditing.

---

## Requirements

### Functional Requirements
1. **Hardware Device Attestation**: Every critical operation (e.g., payment submission, high-value transaction) must send an Apple App Attest challenge token signed by the Secure Enclave to prove app integrity.
2. **Biometric Key Protection**: Sensitive user keys (e.g., private E2EE key or Auth refresh token) must require Touch ID / Face ID authentication before being decrypted.
3. **Transparent Data Encryption**: Select at-rest encryption from the threat model. SQLCipher documents AES-256-CBC page encryption and HMAC integrity protection, not AES-GCM. See [SQLCipher design](https://www.zetetic.net/sqlcipher/design/).
4. **Strict Certificate Pinning**: Evaluate optional pinning against the threat model and rotation requirements while preserving normal TLS trust validation.
5. **Jailbreak / Debugger Anti-Tamper**: Detect Frida hook injection, lldb debugger attachment, or jailbreak binaries (`/Applications/Cydia.app`) and terminate sensitive sessions.

### Non-Functional Requirements

Define and measure these dimensions for the actual workload; values require evidence under [the evidence standard](evidence-and-sources.md):

- Secure Enclave Key Gen Time
- Biometric Auth Prompt Latency
- SQLCipher AES Encryption Overhead
- SPKI TLS Pinning Handshake Time
- App Attest Token Size


---

## High-Level Architecture (HLD)

### Component Diagram

```ascii
+-----------------------------------------------------------------------------------+
|                                  iOS Client Application                           |
|                                                                                   |
|  +-----------------------+           +-----------------------------------------+  |
|  |     User Actions      | --------> |     App Attest & Security Engine        |  |
|  | (Payments, Key Exch)  |           +--------------------+--------------------+  |
|  +-----------------------+                                |                       |
|                                                           v                       |
|                                      +-----------------------------------------+  |
|                                      |      Secure Enclave (SEP Coprocessor)   |  |
|                                      |  - Hardware P-256 Elliptic Curve Keys   |  |
|                                      |  - FaceID / TouchID Gated Key Release    |  |
|                                      +--------------------+--------------------+  |
|                                                           |                       |
|                                                           v                       |
|  +-----------------------+           +-----------------------------------------+  |
|  |   Encrypted Storage   | <-------  |      SPKI Pinning Network Layer         |  |
|  |  (SQLCipher 256-bit   |           |  - TLS 1.3 Handshake Validation        |  |
|  |   Keychain Key)       |           |  - Public Key Hash Verification         |  |
|  +-----------------------+           +--------------------+--------------------+  |
+-----------------------------------------------------------|-----------------------+
                                                            | HTTPS / Attest Token
                                                            v
                                            +-------------------------------+
                                            |       Cloud API Gateway       |
                                            | (Apple Attest Server Verify)  |
                                            +-------------------------------+
```

---

## Deep Dives

### Subsystem 1: Hardware-Backed Key Derivation via Secure Enclave

The Secure Enclave Coprocessor (SEP) generates and isolates 256-bit Elliptic Curve (P-256) private keys in hardware. The raw private key material *never* enters main application memory (RAM).

```swift
import Foundation
import LocalAuthentication
import Security

public final class SecureEnclaveKeyManager {
    public static let shared = SecureEnclaveKeyManager()
    private init() {}
    
    /// Generates a private key inside the Secure Enclave protected by Face ID / Touch ID
    public func generateHardwareProtectedKey(tag: String) throws -> SecKey {
        let accessControl = SecAccessControlCreateWithFlags(
            kCFAllocatorDefault,
            kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            [.privateKeyUsage, .userVerification], // Requires FaceID/TouchID/Passcode
            nil
        )
        
        guard let flags = accessControl else {
            throw SecurityError.accessControlCreationFailed
        }
        
        let attributes: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
            kSecAttrKeySizeInBits as String: 256,
            kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave, // Hardware SEP!
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: tag.data(using: .utf8)!,
                kSecAttrAccessControl as String: flags
            ]
        ]
        
        var error: Unmanaged<CFError>?
        guard let privateKey = SecKeyCreateRandomKey(attributes as CFDictionary, &error) else {
            throw error!.takeRetainedValue() as Error
        }
        
        return privateKey
    }
}

enum SecurityError: Error {
    case accessControlCreationFailed
}
```

---

### Subsystem 2: Device Attestation via DCAppAttestService

Apple's App Attest framework prevents API spoofing by validating that network calls originate from a genuine, un-tampered app running on an authentic iOS device.

```swift
import Foundation
import DeviceCheck
import CryptoKit

public actor AppAttestCoordinator {
    private let service = DCAppAttestService.shared
    private var keyId: String?
    
    /// Generates hardware attestation key and gets attestation object from Apple
    public func createAttestationStatement(challenge: Data) async throws -> (keyId: String, attestationObject: Data) {
        guard service.isSupported else {
            throw SecurityError.attestationNotSupported
        }
        
        // 1. Generate new attestation key pair in Secure Enclave
        let generatedKeyId = try await service.generateKey()
        
        // 2. Hash server challenge (SHA256)
        let challengeHash = Data(SHA256.hash(data: challenge))
        
        // 3. Attest key with Apple servers
        let attestation = try await service.attestKey(generatedKeyId, clientDataHash: challengeHash)
        
        self.keyId = generatedKeyId
        return (generatedKeyId, attestation)
    }
}

extension SecurityError {
    static let attestationNotSupported = SecurityError.accessControlCreationFailed
}
```

---

### Subsystem 3: TLS trust and optional pinning
Validate the platform certificate chain and hostname first. If the threat model calls for pinning, compare the intended certificate or correctly encoded SubjectPublicKeyInfo and define backup pins and a tested rotation plan. Raw bytes returned by SecKeyCopyExternalRepresentation are not automatically DER SubjectPublicKeyInfo. The removed sketch incorrectly treated those encodings as interchangeable.

Pinning is an additional operational commitment, not a universal requirement for every endpoint. A certificate renewal may retain or change its key. Account for both cases and for supported clients that cannot immediately update. Do not bypass normal trust evaluation or invent a cryptographic encoding.

## Edge Cases & Failure Modes

1. **Jailbreak / Frida Hooking**:
   * *Mitigation*: Perform `dlopen` checks for common hooking frameworks (`Substrate`, `FridaGadget`). Check for `PT_DENY_ATTACH` using `ptrace` system calls to disallow debugger attachments.
2. **Secure Enclave Biometric Fallback**:
   * *Mitigation*: If user changes Face ID enrollments (adds new face or resets biometrics), hardware keys bound with `.biometryCurrentSet` are instantly invalidated by the OS, preventing unauthorized access.
3. **App Attest Rate Limiting**:
   * *Mitigation*: Cache the `keyId` locally in Keychain. Do not generate a new key per request; generate key once on install and use `generateAssertion` with a counter for subsequent requests.

---

## FAANG-Style Mock Interview Q&A

### Q1: Why choose SPKI Public Key Pinning over leaf certificate pinning?
**Answer**: Certificate renewal changes certificate bytes and may also change the public key. SPKI pinning follows the key, so key rotation still requires compatible pins. Defend normal TLS trust, backup pins and recovery for old client versions.

---

## Common Mistakes (❌ Wrong $\rightarrow$ ✅ Correct)

- ❌ **Wrong**: Storing secret cryptographic keys in `UserDefaults` or hardcoded inside Swift code string constants.  
  ✅ **Correct**: Generate keys in the hardware **Secure Enclave** (`kSecAttrTokenIDSecureEnclave`) or store in Keychain backed by hardware protection.

- ❌ **Wrong**: Disabling TLS validation during dev testing and shipping to production with `Allow Arbitrary Loads` set to `YES`.  
  ✅ **Correct**: Use platform TLS validation and App Transport Security; add pinning only with a justified threat model and tested rotation and recovery plan.
