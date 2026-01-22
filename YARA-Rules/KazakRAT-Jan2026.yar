rule KazakRAT
{
    meta:
        author = "CtrlAltIntel"
        description = "Identifying known variants of KazakRAT samples"
        date = "03/01/2025"

    strings:
        $uni1 = "exec" ascii wide fullword
        $uni2 = "info" ascii wide fullword
        $uni3 = "disks" ascii wide fullword
        $uni4 = "upload" ascii wide fullword         // All Variants
        $uni5 = "FolderCreated" ascii wide fullword
        $uni6 = "NotCreated" ascii wide fullword
        $uni7 = "x-www-form-urlencoded" ascii wide 

        $dir1 = "dir" ascii wide fullword  // Variant A,C,D
        $dir2 = "aaa" ascii wide fullword // Variant B

    condition:
        uint16(0) == 0x5A4D
        and filesize < 100KB
        and (
            all of ($uni*)
            and any of ($dir*)  
        )
}
