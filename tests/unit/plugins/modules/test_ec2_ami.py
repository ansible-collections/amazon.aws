# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, patch, call

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
        "uefi_data": "QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQa",
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
                UefiData="QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQa"
            )
        ]
    )
