"""
BSD 3-Clause License

Copyright (c) 2021, Netskope OSS
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Tenant Netskope Borderless WAN.
"""

MODULE_NAME = "TENANT"
PLUGIN_VERSION = "1.1.0"
PLATFORM_NAME = "Netskope Borderless WAN"
MAX_API_CALLS = 4
DEFAULT_WAIT_TIME = 60
MAINTENANCE_PULL = "maintenance_pulling"
HISTORICAL_PULL = "historical_pulling"
DEFAULT_WAIT_TIME = 30
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
AUDIT_RECORDS_ENDPOINT = "/v2/auditevents"
TYPE_EVENT = "events"
BACK_PRESSURE_WAIT_TIME = 300
SUBTYPE_LIST_MAPPING = {
    "bwan_audit": "audit",
    "bwan_authentication": "authentication",
    "bwan_client": "client",
    "bwan_gateway": "gateway",
    "bwan_system": "system",
}
SUBTYPE_RESPONSE_MAPPING = {
    "AUDIT": "bwan_audit",
    "AUTHENTICATION": "bwan_authentication",
    "CLIENT": "bwan_client",
    "SYSTEM": "bwan_system",
    "GATEWAY": "bwan_gateway",
}
