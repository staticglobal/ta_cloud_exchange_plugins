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

CrowdStrike Next-Gen SIEM Validator.
"""

import traceback

from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


class CrowdStrikeNGSIEMValidator(object):
    """CrowdStrike Next-Gen SIEM plugin validator class."""

    def __init__(self, logger, log_prefix):
        """CrowdStrike Next-Gen SIEM validator initializer.

        Args:
            logger (Logger): Logger object.
            log_prefix (str): Log prefix.
        """
        super().__init__()
        self.logger = logger
        self.log_prefix = log_prefix

    def validate_mappings(self, mappings):
        """Read the given mapping string and validates its schema.

        Returns:
            bool: True or False
        """
        # schema for mappings
        schema = {
            "type": "object",
            "properties": {
                "taxonomy": {
                    "type": "object",
                    "properties": {"json": {"type": "object"}},
                    "anyOf": [{"required": ["json"]}],
                }
            },
            "required": ["taxonomy"],
        }

        # If no exception is raised by validate(), the instance is valid.
        try:
            validate(instance=mappings, schema=schema)
            return True
        except JsonSchemaValidationError as err:
            self.logger.error(
                message=(
                    "{}: Error occurred while validating Mapping String. "
                    "Error: {}".format(self.log_prefix, err)
                ),
                details=traceback.format_exc(),
            )
        return False
