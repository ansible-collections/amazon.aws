#!/usr/bin/env python3

from unittest.mock import MagicMock, Mock, patch, call

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami"


@patch(module_name + ".get_image_by_id")
def test_create_image_uefi_data(m_get_image_by_id):
    module = MagicMock()
    connection = MagicMock()

    m_get_image_by_id.return_value = {
        "ImageId": "ami-0c7a795306730b288",
        "BootMode": "uefi",
        "TpmSupport": "v2.0",
        }

    module.params = {
        "name": "my-image",
        "boot_mode": "uefi",
        "tpm_support": "v2.0",
        "uefi_data": "QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQaUjSKeFubSYxJduPsbEp6sSIeKiqolx566aEiRfBvvVk86cWT9OwhSMSTF/Fa34wzyXQzYS30+PtB2Hk7+2Xfvn0zO9+8b7RSQ5H5795bduttqt16fTUuV8yG+hdPs64/XOycjdc6yebcRpycS5bT+MX4rV7cTSc77TTprO6sud04ed/WzaM3Jq6cufj2ezcvPTVS1G3m/2F+criyRte/GDlS1Ctksr7NJQtxMlxZ1usfoJFiKagMGA+eLdq1t+hqr9geu3ZkenSjMfVu+/3v/158vJlddtS9U/k1zi+vxZ1eemCnY3UvLrv9Qqu9VG5nZbx1r32g2H9mtZUudpK1LObgTszTL79UG1VWbpxqnV1ZSjq99sLkatyqjFcU3fPbI7M/n3jz+cs/nf7l828/GB2pTIHp5WTtXCuJp+NWGuZCt4wbi6ILdXGj+8TNtrorZeytRn1smVCFuTLTXikae+bz0MCEeuj/z/jbLiLrhu/gbp/meunSgE7d2VvW9b1xoHFvtnlhUIemkiR0aOaudmjAjD4db2aHzoOVWv3dosLBgc29gYf3Cew7WpvXKqeDJyrZ6EReznQ+v//yaHg2K7nu5ou7Z0P7VGh3wtZKnpOleclIHLY38lrf8ehEuApdiBbD4/HoWNhzLLSa4e94dDJEjRd1A3uGdrhx+KHd4oGoPpet+1Rjt50h5zfX45l2diDn2ddzxc79KrLKSqyyMiuf/oeKM8ih3eO8vxqssXc4j75aGc4jNQnsdEjts+Fbzp/J6sjuLJGt+/Dl/ZOt65e2r370x8Xvtq5/uX3l0+2vr/7+8RfbP3yz/uc7n3XTkHv21p9pd9+4v/wJ2smlX/vrw7FX/rk88dWT55uf/Lj566DaEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA7pp/ASh7g9o=",
    }

    ec2_ami.create_image(module, connection)
    assert connection.register_image.call_count == 1
    connection.register_image.assert_has_calls(
        [
            call(
                aws_retry=True,
                Description=None,
                Name="my-image",
                BootMode="uefi",
                TpmSupport="v2.0",
                UefiData="QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQaUjSKeFubSYxJduPsbEp6sSIeKiqolx566aEiRfBvvVk86cWT9OwhSMSTF/Fa34wzyXQzYS30+PtB2Hk7+2Xfvn0zO9+8b7RSQ5H5795bduttqt16fTUuV8yG+hdPs64/XOycjdc6yebcRpycS5bT+MX4rV7cTSc77TTprO6sud04ed/WzaM3Jq6cufj2ezcvPTVS1G3m/2F+criyRte/GDlS1Ctksr7NJQtxMlxZ1usfoJFiKagMGA+eLdq1t+hqr9geu3ZkenSjMfVu+/3v/158vJlddtS9U/k1zi+vxZ1eemCnY3UvLrv9Qqu9VG5nZbx1r32g2H9mtZUudpK1LObgTszTL79UG1VWbpxqnV1ZSjq99sLkatyqjFcU3fPbI7M/n3jz+cs/nf7l828/GB2pTIHp5WTtXCuJp+NWGuZCt4wbi6ILdXGj+8TNtrorZeytRn1smVCFuTLTXikae+bz0MCEeuj/z/jbLiLrhu/gbp/meunSgE7d2VvW9b1xoHFvtnlhUIemkiR0aOaudmjAjD4db2aHzoOVWv3dosLBgc29gYf3Cew7WpvXKqeDJyrZ6EReznQ+v//yaHg2K7nu5ou7Z0P7VGh3wtZKnpOleclIHLY38lrf8ehEuApdiBbD4/HoWNhzLLSa4e94dDJEjRd1A3uGdrhx+KHd4oGoPpet+1Rjt50h5zfX45l2diDn2ddzxc79KrLKSqyyMiuf/oeKM8ih3eO8vxqssXc4j75aGc4jNQnsdEjts+Fbzp/J6sjuLJGt+/Dl/ZOt65e2r370x8Xvtq5/uX3l0+2vr/7+8RfbP3yz/uc7n3XTkHv21p9pd9+4v/wJ2smlX/vrw7FX/rk88dWT55uf/Lj566DaEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA7pp/ASh7g9o="
            )
        ]
    )
