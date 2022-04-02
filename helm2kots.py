#!/usr/bin/env python

import yaml
import re
import copy

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
    with open("values_stackstate.yaml", "r") as stream:
        try:
            input_helm_values = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    make_group("top_options", "Top Options", "Top-Level Options")
    for key in input_helm_values:
        if type(input_helm_values.get(key)) == dict:
            make_group(key, key, key)
        key_array=[key]
        build_options(key_array)
    #print(output_kots_config_yaml)
    #print("\n\n\n")
    #print(yaml.dump(output_kots_helm_values))

def build_options(key_array):
    if len(key_array) <= 1:
        parent_key_array = None
    else:
        parent_key_array = key_array[0:len(key_array) - 1]

    global input_helm_values
    value = get_value_from_yaml_key_notation(key_array)
    value_type = type(value)
    if value_type == dict:
        if get_value_from_yaml_key_notation(key_array) == {}:
            print ("ERROR: {} - Cannot have an empty map as a value".format(get_key_string(key_array)))
            return

        # TODO: Split the dictionary by types so they go first - maps and other

        make_config_options (
            key_array,
            "Customize ",
            "TODO",
            "bool",
            "0",
            parent_key_array
            )
        for child_key in value:
            child_key_array = copy.deepcopy(key_array)
            child_key_array.append(child_key)
            # print("child_key_array: {}, key_array: {}".format(child_key_array, key_array))
            build_options(child_key_array)
        return
    if value_type == str:
        make_config_options (
            key_array,
            "Set ",
            "TODO",
            "text",
            value,
            parent_key_array
            )
        return
    if value_type == float or value_type == int:
        make_config_options (
            key_array,
            "Set ",
            "TODO",
            "text",
            value,
            parent_key_array
            )
        return
    if value_type == bool:
        make_config_options (
            key_array,
            "Set ",
            "TODO",
            "bool",
            value,
            parent_key_array
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
    return re.sub(r'_{1,}', '_', non_camel_case)

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

def make_config_options(key_array, title_lead, help_text, type, default, parent_key_array):
    global output_kots_config_yaml
    helm_key = get_key_string(key_array)

    template_name = to_snake_case(helm_key)
    when_key = to_snake_case(get_key_string(parent_key_array))



    output_kots_config_yaml += str(
'''
      - name: "{}"
        title: "{}"
        help_text: "{}"
        type: "{}"
        default: "{}"
'''.format(template_name, title_lead + helm_key.capitalize(), help_text, type, default, when_key)
    )
    if when_key != "":
        output_kots_config_yaml += '        when: repl{{ ConfigOptionEquals "' + when_key + '" "1" }}'

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

    #print("ERROR: {} - not added to helm values output - not acceptable type: {}".format(get_key_string(key_array), type))

def make_group(name, title, description):
    global output_kots_config_yaml
    output_kots_config_yaml += str(
'''
    - name: {}
      title: {}
      description: {}
      items:
'''.format(name, title, description)
    )

main()
