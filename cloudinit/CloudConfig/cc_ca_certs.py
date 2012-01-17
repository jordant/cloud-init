# vi: ts=4 expandtab
#
#    Author: Mike Milner <mike.milner@canonical.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import pwd
import socket
from subprocess import check_call
import json
import StringIO
import ConfigParser
import cloudinit.CloudConfig as cc
import cloudinit.util as util

CA_CERT_PATH = "/usr/share/ca-certificates/"
CA_CERT_FILENAME = "cloud-init-ca-certs.crt"
CA_CERT_CONFIG = "/etc/ca-certificates.conf"
CA_CERT_SYSTEM_PATH = "/etc/ssl/certs/"

def write_file(filename, contents, owner, group, mode):
    """
    Write a file to disk with specified owner, group, and mode. If the file
    exists already it will be overwritten.

    @param filename: Full path to the new file.
    @param contents: The contents of the newly created file.
    @param owner: The username who should own the file.
    @param group: The group for the new file.
    @param mode: The octal mode (as string) for the new file.
    """
    raise NotImplementedError()

def append_to_file(filename, contents):
    """
    Append C{contents} to an existing file on the filesystem. If the file
    doesn't exist it will be created with the default owner and permissions.

    @param filename: Full path to the new file.
    @param contents: The contents to append to the file.
    """
    raise NotImplementedError()

def delete_dir_contents(dirname):
    """
    Delete all the contents of the directory specified by C{dirname} without
    deleting the directory itself.

    @param dirname: The directory whose contents should be deleted.
    """
    raise NotImplementedError()

def update_ca_certs():
    """
    Updates the CA certificate cache on the current machine.
    """
    check_call(["update-ca-certificates"])

def add_ca_certs(certs):
    """
    Adds certificates to the system. To actually apply the new certificates
    you must also call L{update_ca_certs}.

    @param certs: A list of certificate strings.
    """
    if certs:
        cert_file_contents = "\n".join(certs)
        cert_file_fullpath = os.path.join(CA_CERT_PATH, CA_CERT_FILENAME)
        write_file(cert_file_fullpath, cert_file_contents, "root", "root", "644")
        append_to_file(CA_CERT_CONFIG, CA_CERT_FILENAME) 

def remove_default_ca_certs():
    """
    Removes all default trusted CA certificates from the system. To actually
    apply the change you must also call L{update_ca_certs}.
    """
    delete_dir_contents(CA_CERT_PATH)
    delete_dir_contents(CA_CERT_SYSTEM_PATH)
    write_file(CA_CERT_CONFIG, "", "root", "root", "644")

def handle(name, cfg, cloud, log, args):
    """
    Call to handle ca-cert sections in cloud-config file.

    @param name: The module name "ca-cert" from cloud.cfg
    @param cfg: A nested dict containing the entire cloud config contents.
    @param cloud: The L{CloudInit} object in use.
    @param log: Pre-initialized Python logger object to use for logging.
    @param args: Any module arguments from cloud.cfg
    """
    # If there isn't a ca-certs section in the configuration don't do anything
    if not cfg.has_key('ca-certs'):
        return
    ca_cert_cfg = cfg['ca-certs']

    # If there is a remove-defaults option set to true, remove the system
    # default trusted CA certs first.
    if ca_cert_cfg.get("remove-defaults", False):
        remove_default_ca_certs()

    # If we are given any new trusted CA certs to add, add them.
    if ca_cert_cfg.has_key('trusted'):
        trusted_certs = util.get_cfg_option_list_or_str(ca_cert_cfg, 'trusted')
        if trusted_certs:
            add_ca_certs(trusted_certs)

    # Update the system with the new cert configuration.
    update_ca_certs()
