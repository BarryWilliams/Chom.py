#!/usr/bin/env python3

#########
# The following program contains material that may be disturbing.
# Viewer discretion is advised


# TODO
# pull comments and use as descriptions

# NOTE TO USER: You will still need to clean up the config screen, and possibly
# do some debugging on the rendered objects

import yaml
import re
import copy
import sys

# init
input_helm_values={}

output_kots_helm_values = {}

output_kots_config_yaml = str(
'''
apiVersion: kots.io/v1beta1
kind: Config
metadata:
  name: config-sample
spec:
  groups:
'''
)

def main():
    global input_helm_values

    args = sys.argv
    if len(args) <= 1:
        print("Please provide the name and path of the helm values file as the first argument")
        sys.exit(1)
    input_values_file = args[1]

    with open(input_values_file, "r") as stream:
        try:
            input_helm_values = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    make_group(["top.options"], [], "")

    # Make sure dictionary types are rendered last
    child_keys = []
    for ck in input_helm_values.keys():
        ck_array = [ck]
        if type(get_value_from_yaml_key_notation(ck_array)) == dict:
            child_keys.append(ck)
        else:
            child_keys.insert(0, ck)

    for key in child_keys:
        build_options([key], [])

    #add indentation to values file to make easy copy-paste
    output_kots_helm_values_formatted_splitlines = yaml.dump(output_kots_helm_values).splitlines()
    for i in range(len(output_kots_helm_values_formatted_splitlines)):
        output_kots_helm_values_formatted_splitlines[i] = "    " +  output_kots_helm_values_formatted_splitlines[i]
    output_kots_helm_values_formatted = "\n".join(output_kots_helm_values_formatted_splitlines)


    output_kots_config_file = open("{}.kots_config.yaml".format(input_values_file), "w")
    output_kots_config_file.write(output_kots_config_yaml)
    output_kots_config_file.close()

    output_kots_config_file = open("{}.kots_helm_values.yaml".format(input_values_file), "w")
    output_kots_config_file.write(output_kots_helm_values_formatted)
    output_kots_config_file.close()

def build_options(key_array, when_key_array):
    global input_helm_values
    key_name = key_array[len(key_array) - 1]
    value = get_value_from_yaml_key_notation(key_array)
    value_type = type(value)
    if value_type == dict:
        if get_value_from_yaml_key_notation(key_array) == {}:
            print ("ERROR: {} - Cannot have an empty map as a value".format(get_key_string(key_array)))
            return
        modified_key_array = copy.deepcopy(key_array)
        modified_key_array[len(modified_key_array) - 1] = modified_key_array[len(modified_key_array) - 1] + "_menu_bool"

        make_group(key_array, when_key_array, "")
        make_config_options (
            modified_key_array,
            "Customize " + human_print(key_array),
            '',
            "bool",
            False,
            when_key_array
            )

        # render dictionary items last
        child_keys = []
        for ck in value:
            ck_array = copy.deepcopy(key_array)
            ck_array.append(ck)
            if type(get_value_from_yaml_key_notation(ck_array)) == dict:
                child_keys.append(ck)
            else:
                child_keys.insert(0, ck)

        for ck in child_keys:
            child_key_array = copy.deepcopy(key_array)
            child_key_array.append(ck)
            new_when_key_array = copy.deepcopy(when_key_array)
            new_when_key_array.append(to_snake_case(get_key_string(key_array)) + "_menu_bool")
            build_options(child_key_array, new_when_key_array)
        return
    if value_type == str:
        make_config_options (
            key_array,
            "Set " + human_print(key_array),
            '',
            "text",
            value,
            when_key_array
            )
        return
    if value_type == float or value_type == int:
        make_config_options (
            key_array,
            "Set " + human_print(key_array),
            '',
            "text",
            value,
            when_key_array
            )
        return
    if value_type == bool:
        make_config_options (
            key_array,
            "Set " + human_print(key_array),
            '',
            "bool",
            value,
            when_key_array
            )
        return
    if value_type == type(None):
        print ("ERROR: {} - cannot convert a Null value".format(get_key_string(key_array)))
        return

### UGLY FORMATTING STUFF ###
def to_snake_case(text):
    # Remove any non alphanumeric
    alphanumeric = re.sub(r'[^a-zA-Z\d]', '_', text)

    # Convert any Camel Case
    non_camel_case = re.sub(r'(?<!^)(?=[A-Z])', '_', alphanumeric).lower()

    # Strip excess underscores
    snaked = re.sub(r'_{1,}', '_', non_camel_case)
    return snaked

def get_key_string(key_array):
    if key_array == None:
        return ""
    return '.'.join(key_array)

def get_value_from_yaml_key_notation(key_array):
    global input_helm_values
    if len(key_array) == 0:
        return None
    i = input_helm_values
    for k in key_array:
        i = i[k]
    return i

def make_config_options(key_array, title, help_text, type, default, when_key_array):
    global output_kots_config_yaml
    helm_key = get_key_string(key_array)
    template_name = to_snake_case(helm_key)
    when_string = form_when_string(when_key_array)

    if type == "bool":
        if default == True:
            default = "1"
        else:
            default = "0"
    output_kots_config_yaml += str(
'''
      - name: "{}"
        title: "{}"
        help_text: "{}"
        type: "{}"
        default: '{}'
'''.format(template_name, title, help_text, type, default)
    )
    if when_string != "":
        output_kots_config_yaml += "        when: " + when_string

    #add to helm values output
    global output_kots_helm_values

    # ensure path exists
    i = output_kots_helm_values
    for k in key_array[0:len(key_array)]:
        if k not in i:
            i[k] = {}
        i=i[k]

    # switch by type
    key_to_insert = key_array[len(key_array)-1]

    value_to_insert = 'repl{{ ConfigOption `kots_template_name`}}'.replace("kots_template_name", template_name)
    i[key_to_insert] = value_to_insert

def make_group(key_array, when_array, description):
    global output_kots_config_yaml
    key_name = get_key_string(key_array)
    title = human_print(key_array)

    output_kots_config_yaml += str(
'''
    - name: {}
      title: "{}"
      description: "{}"
'''.format(to_snake_case(key_name), title, description)
    )
    when_string = form_when_string(when_array)
    if when_string != "":
        output_kots_config_yaml += "      when: " + when_string + "\n"
    output_kots_config_yaml += "      items:\n"

def form_when_string(when_array):
    if len(when_array) == 0:
        return ""
    return "'repl{{ " + form_when_string_inner(when_array) + " }}'"

def form_when_string_inner(when_array):
    if len(when_array) == 0:
        return ""

    if len(when_array) == 1:
        return '(ConfigOptionEquals "' + to_snake_case(when_array[0]) + '" "1")'

    if len(when_array) == 2:
        return '(and (ConfigOptionEquals "' + to_snake_case(when_array[0]) + '" "1") (ConfigOptionEquals "' + to_snake_case(when_array[1]) + '" "1"))'

    when_array.pop(0)
    return '(and ' + form_when_string_inner(when_array) + ')'

def human_print(key_array):
    first_name = ""
    second_name = ""
    if len(key_array) == 0:
        return ""
    if len(key_array) == 1:
        first_name = key_array[0]
    if len(key_array) >= 2:
        first_name = key_array[len(key_array) - 2]
        second_name = key_array[len(key_array) - 1]
    title = ' '.join([first_name, second_name])

    # pretty format
    title = to_snake_case(title)
    title = re.sub(r'_', ' ', title).title()
    return title

main()
