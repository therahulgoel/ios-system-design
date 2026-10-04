# Mobile Security, Cryptography & Zero-Trust Engine

## Overview
For Staff, Principal, and Engineering Manager roles across fintech (Stripe, Square, PayPal), ride-sharing (Uber, Lyft), and privacy-first platforms (Apple, Signal, Meta), **Mobile Security Architecture & Cryptography** is a critical system design topic. This specification covers client-side Zero-Trust security, hardware-backed key management (Secure Enclave / SEP), App Attestation (Apple DeviceCheck / App Attest), Certificate Pinning (SPKI), local storage encryption (SQLCipher / AES-GCM-256), and anti-tamper runtime protection.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Stripe / Block | Payment tokenization, secure element integration, hardware key derivation | ★★★★★ |
| Apple | Secure Enclave, App Attest, Keychain architecture, system-level privacy | ★★★★★ |
| Meta / Signal | End-to-End Encryption (E2EE), Signal Protocol key management, zero-trust APIs | ★★★★★ |
| Uber / DoorDash | Fraud detection, API key anti-tamper, device integrity verification | ★★★★☆ |
| Google | Play Integrity API, Android Keystore, SafetyNet attestation | ★★★★☆ |

---

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
3. **Transparent Data Encryption**: SQLite databases storing user messages or PII must be encrypted at rest using 256-bit AES-GCM (SQLCipher).
4. **Strict Certificate Pinning**: All network requests must validate the server's public key hash against an embedded SPKI hash, failing instantly on MITM interception.
5. **Jailbreak / Debugger Anti-Tamper**: Detect Frida hook injection, lldb debugger attachment, or jailbreak binaries (`/Applications/Cydia.app`) and terminate sensitive sessions.

### Non-Functional Requirements
| Requirement | Target | Source / Authoritative Benchmark |
| :--- | :--- | :--- |
| Secure Enclave Key Gen Time | $< 80\text{ms}$ | Apple Secure Enclave Hardware Spec |
| Biometric Auth Prompt Latency | $< 400\text{ms}$ | LocalAuthentication Framework Latency |
| SQLCipher AES Encryption Overhead | $< 5\%$ read/write CPU overhead | SQLCipher Performance Benchmarks |
| SPKI TLS Pinning Handshake Time | $< 50\text{ms}$ overhead | Apple URLSession Security Benchmark |
| App Attest Token Size | $< 2\text{KB}$ CBOR payload | Apple App Attest Documentation |

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

### Subsystem 3: SPKI Certificate Pinning (URLSessionDelegate)

Subject Public Key Info (SPKI) pinning extracts the SHA-256 hash of the server's public key during the TLS handshake. Unlike certificate leaf pinning, SPKI pinning survives server certificate renewals as long as the underlying public key remains rotated safely.

```swift
import Foundation
import CryptoKit

public final class SPKIPinningDelegate: NSObject, URLSessionDelegate {
    private let pinnedPublicKeyHashes: Set<String> // Base64 SHA-256 hashes of server SPKI
    
    public init(pinnedPublicKeyHashes: Set<String>) {
        self.pinnedPublicKeyHashes = pinnedPublicKeyHashes
    }
    
    public func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Validate TLS Server Trust chain
        var error: CFError?
        guard SecTrustEvaluateWithError(serverTrust, &error) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Extract server public key from certificate chain
        guard let certificateChain = SecTrustCopyCertificateChain(serverTrust) as? [SecCertificate],
              let leafCertificate = certificateChain.first,
              let publicKey = SecCertificateCopyKey(leafCertificate),
              let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, nil) as Data? else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Calculate SHA-256 Hash of Public Key
        let hash = Data(SHA256.hash(data: publicKeyData)).base64EncodedString()
        
        if pinnedPublicKeyHashes.contains(hash) {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            print("[Security Failure] SPKI Pinning mismatch! Server hash: \(hash)")
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

---

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
**Answer**: Leaf certificate pinning breaks the mobile application whenever the server SSL certificate is renewed (typically every 90 days with Let's Encrypt). SPKI pins the SHA-256 hash of the Subject Public Key Info. Since servers keep the same public key pair across certificate renewals, SPKI pinning prevents client outage while preserving strict TLS 1.3 MITM protection.

---

## Common Mistakes (❌ Wrong $\rightarrow$ ✅ Correct)

- ❌ **Wrong**: Storing secret cryptographic keys in `UserDefaults` or hardcoded inside Swift code string constants.  
  ✅ **Correct**: Generate keys in the hardware **Secure Enclave** (`kSecAttrTokenIDSecureEnclave`) or store in Keychain backed by hardware protection.

- ❌ **Wrong**: Disabling TLS validation during dev testing and shipping to production with `Allow Arbitrary Loads` set to `YES`.  
  ✅ **Correct**: Enforce App Transport Security (ATS) with SPKI certificate pinning across all production API endpoints.
