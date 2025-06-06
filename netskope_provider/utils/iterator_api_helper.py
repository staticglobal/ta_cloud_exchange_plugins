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

Tenant Netskope Plugin helper module.
"""

import json
import re
import traceback
import time
from typing import Dict, Union
from requests.exceptions import ReadTimeout

import requests
from netskope.common.utils import add_user_agent
from .constants import (
    PLATFORM_NAME,
    MODULE_NAME,
    MAX_API_CALLS,
    DEFAULT_WAIT_TIME,
    CLIENT_STATUS_ITERATOR_NAME
)

from netskope.common.utils.plugin_provider_helper import PluginProviderHelper
plugin_provider_helper = PluginProviderHelper()


class NetskopeProviderPluginException(Exception):
    """Netskope Provider plugin custom exception class."""

    pass

class IteratorAlreadyExists(Exception):
    """Iterator already exists custom exception class."""

    pass

class NetskopePluginHelper(object):
    """NetskopePluginHelper class.

    Args:
        object (object): Object class.
    """

    def __init__(
        self,
        logger,
        log_prefix: str,
        plugin_name: str,
        plugin_version: str
    ):
        """Netskope Provider Plugin Helper initializer.

        Args:
            logger (logger object): Logger object.
            log_prefix (str): log prefix.
            plugin_name (str): Plugin name.
            plugin_version (str): Plugin version.
        """
        self.log_prefix = log_prefix
        self.logger = logger
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version

    def _add_user_agent(self, headers: Union[Dict, None] = None) -> Dict:
        """Add User-Agent in the headers for third-party requests.

        Args:
            headers (Dict): Dictionary containing headers for any request.
        Returns:
            Dict: Dictionary after adding User-Agent.
        """
        if headers and "User-Agent" in headers:
            return headers
        headers = add_user_agent(headers)
        ce_added_agent = headers.get("User-Agent", "netskope-ce")
        user_agent = "{}-{}-{}-v{}".format(
            ce_added_agent,
            MODULE_NAME.lower(),
            self.plugin_name.replace(" ", "-").lower(),
            self.plugin_version,
        )
        headers.update({"User-Agent": user_agent})
        return headers

    def api_helper(
        self,
        logger_msg: str,
        url: str,
        method: str = "GET",
        params: Dict = {},
        data=None,
        files=None,
        headers: Dict = {},
        verify=True,
        proxies=None,
        json=None,
        is_handle_error_required=True,
        is_validation=False,
        regenerate_auth_token=True,
    ):
        """API Helper to perform API request on ThirdParty platform \
        and captures all the possible errors for requests.

        Args:
            logger_msg (str): Logger message.
            url (str): API Endpoint.
            method (str): Method for the endpoint.
            params (Dict, optional): Request parameters dictionary.
            Defaults to None.
            data (Any,optional): Data to be sent to API. Defaults to None.
            headers (Dict, optional): Headers for the request. Defaults to {}.
            json (optional): Json payload for request. Defaults to None.
            is_handle_error_required (bool, optional): Does the API helper
            should handle the status codes. Defaults to True.
            is_validation (bool, optional): Does this request coming from
            validate method?. Defaults to False.
            regenerate_auth_token (bool, optional): Is regenerating auth token
            required? Defaults to True.
            configuration (Dict): Configuration Dictionary.


        Returns:
            Response|Response JSON: Returns response json if
            is_handle_error_required is True otherwise returns Response object.
        """
        try:
            headers = self._add_user_agent(headers)
            debug_log_msg = (
                f"{self.log_prefix}: API Request for {logger_msg}."
                f" Endpoint: {method} {url}"
            )
            if params:
                debug_log_msg += f", params: {params}."

            self.logger.debug(debug_log_msg)
            for retry_counter in range(MAX_API_CALLS):
                response = requests.request(
                    url=url,
                    method=method,
                    params=params,
                    data=data,
                    headers=headers,
                    verify=verify,
                    proxies=proxies,
                    json=json,
                    files=files,
                )
                status_code = response.status_code
                if not is_validation and status_code != 404:
                    self.logger.debug(
                        f"{self.log_prefix}: Received API Response for "
                        f"{logger_msg}. Status Code={status_code}."
                    )
                if status_code == 429 and not is_validation:
                    if retry_counter == MAX_API_CALLS - 1:
                        err_msg = (
                            f"Received exit code {status_code}, API rate "
                            f"limit exceeded while {logger_msg}. Max "
                            "retries for rate limit handler exceeded "
                            "hence returning status code 429."
                        )
                        if hasattr(response, "text"):
                            api_resp = response.text
                        else:
                            api_resp = response

                        self.logger.error(
                            message=f"{self.log_prefix}: {err_msg}",
                            details=f"API response: {api_resp}",
                        )
                        raise NetskopeProviderPluginException(err_msg)
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if retry_after > 300:
                        err_msg = (
                            "'Retry-After' value received from "
                            f"response headers while {logger_msg} is greater "
                            f" than 5 minutes hence "
                            f"returning status code {status_code}."
                        )
                        if hasattr(response, "text"):
                            api_resp = response.text
                        else:
                            api_resp = response
                        self.logger.error(
                            message=f"{self.log_prefix}: {err_msg}",
                            details=f"API response: {api_resp}",
                        )
                        raise NetskopeProviderPluginException(err_msg)
                    self.logger.error(
                        message=(
                            f"{self.log_prefix}: Received exit code 429, "
                            f"API rate limit exceeded while {logger_msg}. "
                            f"Retrying after {retry_after} "
                            f"seconds. {MAX_API_CALLS - 1 - retry_counter} "
                            "retries remaining."
                        )
                    )
                    time.sleep(retry_after)
                elif (
                    (500 <= status_code <= 600)
                    and not is_validation
                    and "permission denied" not in response.text
                ):
                    if retry_counter == MAX_API_CALLS - 1:
                        err_msg = (
                            f"Received exit code {status_code}, while "
                            f" {logger_msg}. Max retries for rate limit "
                            "handler exceeded hence returning status"
                            f" code {status_code}."
                        )
                        if hasattr(response, "text"):
                            api_resp = response.text
                        else:
                            api_resp = response
                        self.logger.error(
                            message=f"{self.log_prefix}: {err_msg}",
                            details=f"API response: {api_resp}",
                        )
                        raise NetskopeProviderPluginException(err_msg)

                    self.logger.error(
                        message=(
                            f"{self.log_prefix}: Received exit code "
                            f"{status_code}, HTTP server error occurred while "
                            f"{logger_msg}. Retrying after {DEFAULT_WAIT_TIME}"
                            f" seconds. {MAX_API_CALLS - 1 - retry_counter}"
                            " retries remaining."
                        ),
                    )
                    time.sleep(DEFAULT_WAIT_TIME)

                else:
                    return (
                        self.handle_error(response, logger_msg, is_validation)
                        if is_handle_error_required
                        else response
                    )
        except IteratorAlreadyExists:
            raise
        except ReadTimeout as error:
            err_msg = f"Read Timeout error occurred while {logger_msg}."
            self.logger.error(
                message=f"{self.log_prefix}: {err_msg} Error: {error}",
                details=str(traceback.format_exc()),
            )
            raise NetskopeProviderPluginException(err_msg)
        except requests.exceptions.ProxyError as error:
            err_msg = (
                f"Proxy error occurred while {logger_msg}. Verify the"
                " proxy configuration provided."
            )
            if is_validation:
                err_msg = (
                    "Proxy error occurred. Verify "
                    "the proxy configuration provided."
                )

            self.logger.error(
                message=f"{self.log_prefix}: {err_msg} Error: {error}",
                details=traceback.format_exc(),
            )
            raise NetskopeProviderPluginException(err_msg)
        except requests.exceptions.ConnectionError as error:
            err_msg = (
                f"Unable to establish connection with {PLATFORM_NAME} "
                f"platform while {logger_msg}. Proxy server or "
                f"{PLATFORM_NAME} server is not reachable."
            )
            if is_validation:
                err_msg = (
                    f"Unable to establish connection with {PLATFORM_NAME} "
                    f"platform. Proxy server or {PLATFORM_NAME}"
                    " server is not reachable."
                )

            self.logger.error(
                message=f"{self.log_prefix}: {err_msg} Error: {error}",
                details=traceback.format_exc(),
            )
            raise NetskopeProviderPluginException(err_msg)
        except requests.HTTPError as err:
            err_msg = f"HTTP error occurred while {logger_msg}."
            if is_validation:
                err_msg = (
                    "HTTP error occurred. Verify"
                    " configuration parameters provided."
                )
            self.logger.error(
                message=f"{self.log_prefix}: {err_msg} Error: {err}",
                details=traceback.format_exc(),
            )
            raise NetskopeProviderPluginException(err_msg)
        except NetskopeProviderPluginException:
            raise
        except Exception as exp:
            err_msg = f"Unexpected error occurred while {logger_msg}."
            if is_validation:
                err_msg = (
                    "Unexpected error while performing "
                    f"API call to {PLATFORM_NAME}."
                )
                self.logger.error(
                    message=f"{self.log_prefix}: {err_msg} Error: {exp}",
                    details=traceback.format_exc(),
                )
                raise NetskopeProviderPluginException(
                    f"{err_msg} Check logs for more details."
                )
            self.logger.error(
                message=f"{self.log_prefix}: {err_msg} Error: {exp}",
                details=traceback.format_exc(),
            )
            raise NetskopeProviderPluginException(err_msg)

    def parse_response(self, response, is_validation: bool = False):
        """Parse Response will return JSON from response object.

        Args:
            response (response): Response object.

        Returns:
            Any: Response Json.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as err:
            err_msg = (
                f"Invalid JSON response received from API. Error: {str(err)}"
            )

            if hasattr(response, "text"):
                api_resp = response.text
            else:
                api_resp = response

            self.logger.error(
                message=f"{self.log_prefix}: {err_msg}",
                details=f"API response: {api_resp}",
            )
            if is_validation:
                err_msg = (
                    "Verify V1, V2 API Token provided in the "
                    "configuration parameters. Check logs for more details."
                )
            raise NetskopeProviderPluginException(err_msg)
        except Exception as exp:
            err_msg = (
                "Unexpected error occurred while parsing"
                f" json response. Error: {exp}"
            )
            if hasattr(response, "text"):
                api_resp = response.text
            else:
                api_resp = response

            self.logger.error(
                message=f"{self.log_prefix}: {err_msg}",
                details=f"API response: {api_resp}",
            )
            if is_validation:
                err_msg = (
                    "Unexpected validation error occurred, "
                    "Verify V1, V2 API Token provided in the "
                    "configuration parameters. Check logs for more details."
                )
            raise NetskopeProviderPluginException(err_msg)

    def handle_error(
        self,
        resp: requests.models.Response,
        logger_msg: str,
        is_validation: bool = False,
    ):
        """Handle the different HTTP response code.

        Args:
            resp (requests.models.Response): Response object
            returned from API call.
            logger_msg: logger message.
            is_validation : API call from validation method or not
        Returns:
            dict: Returns the dictionary of response JSON
            when the response code is 200.
        Raises:
            HTTPError: When the response code is not 200.
        """
        status_code = resp.status_code
        validation_msg = "Validation error occurred, "
        error_dict = {
            400: "Received exit code 400, HTTP client error",
            401: "Received exit code 401, Unauthorized",
            403: "Received exit code 403, Forbidden",
            404: "Received exit code 404, Resource not found",
        }
        if is_validation:
            error_dict = {
                400: (
                    "Received exit code 400, Bad Request, Verify the "
                    "Tenant URL, V!, V2 API Token provided in the "
                    "configuration parameters."
                ),
                401: (
                    "Received exit code 401, Unauthorized, Verify the "
                    "V1, V2 API Token provided in the configuration parameters."
                ),
                403: (
                    "Received exit code 403, Forbidden, Verify the "
                    "V1, V2 API Token provided in the configuration parameters. "
                    "Make sure the Auth Token contains all the required "
                    "permissions. Refer the "
                    f"{PLATFORM_NAME} guide for details."
                ),
                404: (
                    "Received exit code 404, Resource not found, Verify "
                    "Tenant URL and V1, V2 API Token "
                    "provided in the configuration parameters."
                ),
            }

        if status_code in [200, 201]:
            if resp:
                if hasattr(resp, "text"):
                    api_resp = resp.text
                else:
                    api_resp = resp
                return self.parse_response(api_resp, is_validation)
            else:
                return
        elif status_code == 204:
            return {}   
        elif (
            status_code == 400
            and "Only one iterator is allowed per event type. Please use the existing iterator"
            in resp.text
        ):
            err_msg = (
                "Cannot create Client Status Iterator. "
                "One iterator already exists for the "
                "Client Status event for your tenant. "
                "Delete the existing iterator to continue."
            )
            if hasattr(resp, "text"):
                api_resp = resp.text
            else:
                api_resp = resp
            if is_validation:
                log_err_msg = validation_msg + err_msg
                self.logger.error(
                    message=f"{self.log_prefix}: {log_err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise IteratorAlreadyExists(err_msg)
            else:
                err_msg = err_msg + " while " + logger_msg + "."
                self.logger.error(
                    message=f"{self.log_prefix}: {err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise IteratorAlreadyExists(err_msg)
        elif status_code in [401, 403]:
            err_msg = error_dict[status_code]
            if hasattr(resp, "text"):
                api_resp = resp.text
            else:
                api_resp = resp
            if is_validation:
                log_err_msg = validation_msg + err_msg
                self.logger.error(
                    message=f"{self.log_prefix}: {log_err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise NetskopeProviderPluginException(err_msg)
            else:
                err_msg = err_msg + " while " + logger_msg + "."
                self.logger.error(
                    message=f"{self.log_prefix}: {err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise NetskopeProviderPluginException(err_msg)
        elif status_code in error_dict:
            err_msg = error_dict[status_code]
            if hasattr(resp, "text"):
                api_resp = resp.text
            else:
                api_resp = resp
            if is_validation:
                log_err_msg = validation_msg + err_msg
                self.logger.error(
                    message=f"{self.log_prefix}: {log_err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise NetskopeProviderPluginException(err_msg)
            else:
                err_msg = err_msg + " while " + logger_msg + "."
                self.logger.error(
                    message=f"{self.log_prefix}: {err_msg}",
                    details=f"API response: {api_resp}",
                )
                raise NetskopeProviderPluginException(err_msg)

        else:
            if hasattr(resp, "text"):
                api_resp = resp.text
            else:
                api_resp = resp
            err_msg = (
                "HTTP Server Error"
                if (status_code >= 500 and status_code <= 600)
                else "HTTP Error"
            )
            self.logger.error(
                message=(
                    f"{self.log_prefix}: Received exit code {status_code}, "
                    f"{err_msg} while {logger_msg}."
                ),
                details=f"API response: {api_resp}",
            )
            raise NetskopeProviderPluginException(err_msg)
        
    def update_storage(self, tenant_name, iterator_name):
        """
        Insert or Update Client Status iterator in storage.

        Args:
            end_time (datetime or str): The new checkpoint time.

        Returns:
            None
        """
        # self.storage["client_status_iterator"] = iterator_name
        update_set = {"client_status_iterator": iterator_name}
        plugin_provider_helper.update_tenant_storage(
            tenant_name, update_set
        )
    
    def create_iterator(
        self,
        tenant_url,
        tenant_configuration_name,
        headers,
        iterator_name,
        proxies=None,
        is_validation=False
    ):
        """
        Create Client Status iterator.

        Args:
            tenant_url (str): The tenant URL.
            tenant_configuration_name (str): The tenant configuration name.
            headers (dict): The headers.
            iterator_name (str): The iterator name.
            proxies (dict, optional): The proxy configuration. Defaults to None.
            is_validation (bool, optional): Whether to suppress error logging. Defaults to False.

        Returns:
            str: The iterator name.
        """
        client_status_endpoint = (
            f"{tenant_url}/api/v2/events/dataexport/iterator/{iterator_name}"
        )
        logger_msg = (
            "Creating Client Status "
            f"iterator with name {iterator_name}"
        )
        params = {"eventtype": "clientstatus"}
        # Create New Iterator - first time plugin is saved or if existing iterator does not exists
        resp = self.api_helper(
            logger_msg=logger_msg,
            url=client_status_endpoint,
            method="POST",
            headers=headers,
            params=params,
            proxies=proxies,
            is_handle_error_required=False,
            is_validation=is_validation,
        )
        if resp.status_code == 202:
            match = re.search(r'(netskope_ce[^\s,]+)', resp.text)
            if match:
                iterator_name = match.group(1)
                log_msg = (
                    "Successfully created Client Status "
                    f"iterator with name {iterator_name}"
                )
                self.update_storage(tenant_configuration_name, iterator_name)
                self.logger.info(
                    f"{self.log_prefix}: {log_msg}"
                )
                return iterator_name
            else:
                error_msg = (
                    "Error while storing Client Status "
                    f"iterator with name {iterator_name} in storage."
                )
                self.logger.error(
                    f"{self.log_prefix}: {error_msg}",
                    details=f"API Response: {resp.text}"
                )
                raise NetskopeProviderPluginException(
                    f"{error_msg}, check logs for details."
                )
        else:
            self.handle_error(
                resp,
                logger_msg,
                is_validation=is_validation
            )
    def check_iterator_status(
        self,
        tenant_hostname,
        headers,
        proxies=None,
        tenant_storage=None
    ):
        """
        This function is used to check the status of the Client status iterator.
        
        Parameters:
        tenant_hostname (str): The tenant hostname.
        headers (dict): The headers to be sent with the API call.
        proxies (dict): The proxy configuration in case of proxy enabled.
        tenant_storage (dict): The tenant configuration storage.
        
        Returns:
        bool: True if the iterator is ready else False.
        """
        client_status_storage = tenant_storage.get(
            "client_status_iterator", ""
        ) if tenant_storage else ""
        if client_status_storage:
            # Check the iterator status
            iterator_name = client_status_storage
        else:
            iterator_name = self.create_iterator(
                tenant_url=tenant_hostname,
                tenant_configuration_name=self.tenant_name,
                headers=headers,
                iterator_name=CLIENT_STATUS_ITERATOR_NAME
            )        
        logger_msg = (
            "Checking status of iterator "
            f"with name {iterator_name}"
        )
        iterator_status_endpoint = (
            f"{tenant_hostname}/api/v2/events/dataexport/iterator/{iterator_name}"
        )
        while True:
            resp = self.api_helper(
                logger_msg=logger_msg,
                url=iterator_status_endpoint,
                method="GET",
                headers=headers,
                proxies=proxies,
                is_handle_error_required=True,
            )
            iterator_state = resp.get("status", "")
            if not iterator_state:
                error_messgae = (
                    f"Failed to validate the status of Client status "
                    f"iterator with name '{iterator_name}'."
                )
                self.logger.error(
                    message=error_messgae,
                    details=f"API Response: {resp}",
                )
                return False
            if iterator_state == "Ready":
                self.logger.debug(
                    f"Successfully validated the status of Client status"
                    f"iterator with name '{iterator_name}'. "
                    "Iterator is ready to fetch the data."
                )
                return True
            elif iterator_state == "InProgress":
                self.logger.debug(
                    "Status of Client status iterator with name "
                    f"'{iterator_name}' is 'in progress'. "
                    "Sleeping for 10 seconds before checking the status."
                )
                time.sleep(10)
            elif iterator_state == "Failed":
                error_messgae = (
                    f"The iterator creation failed for Client status"
                    f"iterator with name '{iterator_name}'. "
                    "Please retry creating the iterator. "
                )
                self.logger.error(
                    message=error_messgae,
                    details=f"API Response: {resp}",
                )
                return False
