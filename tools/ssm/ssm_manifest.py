#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os
import json
import sys
import zipfile
import hashlib
import shutil


def buildssmpkg(pkg_version, ssm_base, ssm_files, ssm_installers, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    file_hash = {}
    for ssm_file in ssm_files.keys():
        zip_file = f"{output_dir}/{ssm_file}.zip"
        ssm_file_path = f"{ssm_base}/{ssm_file}"
        if not os.path.isfile(zip_file):
            shutil.copy(ssm_files[ssm_file], ssm_file_path)
            zf = zipfile.ZipFile(zip_file, mode="w")
            file_list = os.listdir(ssm_file_path)
            for file in file_list:
                zf.write(f"{ssm_file_path}/{file}", file)
            zf.close()
        sha256 = hashlib.sha256()
        with open(zip_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
            file_hash[ssm_file] = sha256.hexdigest()
    ssm_sha256_list = {}
    for ssm_file in ssm_files.keys():
        ssm_file_zip = f"{ssm_base}/{ssm_file}.zip"
        ssm_sha256_list[f"{ssm_file}.zip"] = {
            "checksums": {"sha256": file_hash[ssm_file]}
        }

    manifest = {
        "schemaVersion": "2.0",
        "version": pkg_version,
        "packages": ssm_installers,
        "files": ssm_sha256_list,
    }
    print(json.dumps(manifest))
    with open(f"{output}/manifest.json", "w") as f:
        json.dump(manifest, f)
    return manifest


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} version [base] [build] [output]")
        sys.exit()
    aoc_pkg_ver = sys.argv[1]
    if aoc_pkg_ver.startswith("v"):
        aoc_pkg_ver = aoc_pkg_ver[1:]
    base = "tools/ssm" if len(sys.argv) < 3 else sys.argv[2]
    build = "build" if len(sys.argv) < 4 else sys.argv[3]
    output = "build/packages/ssm" if len(sys.argv) < 5 else sys.argv[4]
    aoc_files = {
        "linux-amd64-rpm": f"{build}/packages/linux/amd64/aws-otel-collector.rpm",
        "linux-arm64-rpm": f"{build}/packages/linux/arm64/aws-otel-collector.rpm",
        "linux-amd64-deb": f"{build}/packages/debian/amd64/aws-otel-collector.deb",
        "linux-arm64-deb": f"{build}/packages/debian/arm64/aws-otel-collector.deb",
        "windows-amd64-msi": f"{build}/packages/windows/amd64/aws-otel-collector.msi",
    }

    aoc_installers = {
        "windows": {"_any": {"x86_64": {"file": "windows-amd64-msi.zip"}}},
        "amazon": {
            "_any": {
                "x86_64": {"file": "linux-amd64-rpm.zip"},
                "arm64": {"file": "linux-arm64-rpm.zip"},
            }
        },
        "ubuntu": {
            "_any": {
                "x86_64": {"file": "linux-amd64-deb.zip"},
                "arm64": {"file": "linux-arm64-deb.zip"},
            }
        },
        "debian": {"_any": {"x86_64": {"file": "linux-amd64-deb.zip"}}},
        "redhat": {
            "_any": {
                "x86_64": {"file": "linux-amd64-rpm.zip"},
                "arm64": {"file": "linux-arm64-rpm.zip"},
            }
        },
        "centos": {"_any": {"x86_64": {"file": "linux-amd64-rpm.zip"}}},
        "suse": {
            "_any": {
                "x86_64": {"file": "linux-amd64-rpm.zip"},
                "arm64": {"file": "linux-arm64-rpm.zip"},
            }
        },
    }
    buildssmpkg(aoc_pkg_ver, base, aoc_files, aoc_installers, output)
