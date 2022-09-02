"""
configuration file related libraries
"""
import logging
import re

log = logging.getLogger('QESAPDEP')


def yaml_to_tfvars_entry(key, value):
    if isinstance(value, (str, int)):
        entry = f'{key} = "{str(value)}"'
    elif isinstance(value, bool):
        entry = f'{key} = "{str(value).lower()}"'
    elif isinstance(value, list):
        entry = '", "'.join(value)
        entry = f'{key} = ["{entry}"]'
    elif isinstance(value, dict):
        param_value = ''
        for dict_key, dict_value in value.items():
            param_value = f'{param_value}\t{dict_key} = "{dict_value}"\n'
        entry = f'{key} = {{\n' \
                f'{param_value}' \
                f'}}'
    else:
        log.error('Unrecognized value type in yaml file: %s = %s', key, value)
        return None
    return entry


def yaml_to_tfvars(yaml_data):
    """ Takes data structure collected from yaml config,
    converts into tfvars format

    Args:
        yaml_data (dict): data structure returned from is_yaml
        tfvars_file (str): path to the target tfvars file

    Returns:
        str: terraform.tfvars content string. None for error.
    """
    config_out = ''
    terraform_variables = yaml_data['terraform']['variables']
    log.debug(yaml_data)
    for key, value in terraform_variables.items():
        entry = yaml_to_tfvars_entry(key, value)
        if entry is None:
            return None
        config_out += f'\n{entry}'

    return config_out


def terraform_yml(configure_data):
    """
    Check if Terraform:variables are present in the config.yaml
    """
    if not configure_data:
        log.error("No configure_data")
        return False

    if 'terraform' not in configure_data:
        log.error("Missing 'terraform' key in configure_data")
        return False

    if configure_data['terraform'] is None:
        log.error("configure_data['terraform'] is empty")
        return False

    if 'variables' not in configure_data['terraform']:
        log.error("Missing 'variables' key in configure_data['terraform'] ")
        return False

    return True


def template_to_tfvars(tfvars_template, configure_data):
    """
    Takes data structure collected from yaml config.
    Values are converted into tfvars format and checked against terraform.tfvars.template.
    Variables from yaml config are overwritten by values from template file.

    Args:
        configure_data (dict): configuration data structure
        tfvars_template (str): path to the tfvars template file

    Returns:
        bool: True(pass)/False(failure)
    """
    log.info("Read %s", tfvars_template)
    with open(tfvars_template, 'r', encoding='utf-8') as filehandler:
        tfvar_content = [f"{line.rstrip()}\n" for line in filehandler.readlines()]
        log.debug("Template:%s", tfvar_content)

        if not terraform_yml(configure_data):
            log.debug("No terraform variables in the configure.yaml to merge")
            return tfvar_content

        log.debug("Config has terraform variables")
        for key, value in configure_data['terraform']['variables'].items():
            key_replace = False
            # Look for key in the template file content
            for index, line in enumerate(tfvar_content):
                if re.search(rf'{key}\s?=.*', line):
                    log.debug("Replace template %s with [%s = %s]", line, key, value)
                    tfvar_content[index] = f"{key} = {value}\n"
                    key_replace = True
            # add the new key/value pair
            if not key_replace:
                log.debug("[k:%s = v:%s] is not in the template, append it", key, value)
                entry = yaml_to_tfvars_entry(key, value)
                if entry is None:
                    return None
                tfvar_content.append(f"{entry}\n")
        log.debug("Result terraform.tfvars:\n%s", tfvar_content)
        return tfvar_content