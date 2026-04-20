rule FudCrypt_Signed_Binary
{
    meta:
        description  = "Detects PE/MSI files signed with certificates tied to known FUD Crypt operator identities. Matches on high-confidence subject DN strings embedded verbatim as PrintableString values in the PKCS#7 Authenticode blob — no pe module or OpenSSL required."
        author       = "Ctrl-Alt-Intel"
        date         = "2026-04-19"
        reference    = "https://ctrlaltintel.com/research/FudCrypt-analysis-1/"
        mitre_attack = "T1553.002, T1588.003"

    strings:
        /*
         * Sanbornton account — identity: RichardPescinski.
         * Signed: verifycall.exe (→ ZoomInstaller.exe), call_verify.exe, verifycall3.exe.
         * Subscription 4ad24843. Tenant 6b7fc5cc. Active at capture 2026-04-06.
         * High confidence — personal name, no legitimate software uses this as a cert subject.
         */
        $id_sanbornton = "RichardPescinski" ascii

        /*
         * magdarosol account — leaf certificate CN matches account handle.
         * Subscription 0b1a4b8c-c65b-40a5-98a7-9f3044a35413. Activated 2026-03-19.
         * High confidence.
         */
        $id_magdarosol = "magdarosol" ascii

        /*
         * Non-ATS revoked certificate — O=Julie Jorgensen, CN=Julie Jorgensen,
         * C=US, ST=Maryland, L=BALTIMORE. Confirmed in operator-delivered binaries.
         * Certificate revoked; RFC 3161 countersignatures on existing signed files remain
         * valid — revocation does not retroactively invalidate delivered payloads.
         * High confidence — no known legitimate software publisher uses this identity.
         */
        $id_julie = "Julie Jorgensen" ascii

        /*
         * Non-ATS active certificate — identity: SAKEENAH BOWIE.
         * Used to sign ScreenConnect installer; installer observed connecting to
         * 179.43.176.32 (FUD Crypt signing VM WIN-8OA3CCQAE4D).
         * High confidence — no known legitimate software publisher uses this identity.
         */
        $id_sakeenah = "SAKEENAH BOWIE" ascii

    condition:
        (uint16(0) == 0x5A4D or uint32(0) == 0xe011cfd0) and
        filesize < 50MB and
        any of ($id_*)
}
