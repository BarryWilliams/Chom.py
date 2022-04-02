import re

test = {
    "hi": {
        "there": "yo"
    },
    "key1":
    {
        "something":"something"
    }
}

key_array = ["key1", "key2", "key3", "object1"]

# ensure path exists
i = test
for k in key_array[0:len(key_array) - 1]:
    if k not in i:
        i[k] = {}
    i = i[k]
print(i)

key_name=key_array[len(key_array)-1 ]
i[key_name] = 'repl{{ ConfigOption `{kots_template_name}`}}'.replace("kots_template_name", "hello")

print(i)
print(test)


template_name="hi"

print('repl{{ ConfigOption `{kots_template_name}`}}'.replace("kots_template_name", template_name))


def to_snake_case(text):
    # Remove any non alphanumeric
    alphanumeric = re.sub(r'[^a-zA-Z\d]', '_', text)

    # Convert any Camel Case
    non_camel_case = re.sub(r'(?<!^)(?=[A-Z])', '_', alphanumeric).lower()

    # Strip excess underscores
    return re.sub(r'_{1,}', '_', non_camel_case)


print(to_snake_case("HiThere__Whadnklst..//?sjkdsa"))
