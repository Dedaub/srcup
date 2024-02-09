class BaseFieldObj():
    def __init__(self, field_name):
        self.field_name = field_name
        self.before: str = ""
        self.contents: str = ""
        self.after: str = ""
        self.exists: bool = False

    def format_field(self) -> str:
        pass

    def parse_string(self, js_string):
        pass


class ListFieldObj(BaseFieldObj):
    def __init__(self, field_name):
        super().__init__(field_name)
        self.must_have_fields = []

    def parse_string(self, js_string):
        exists, self.before, self.contents, self.after = split_on_field_brackets(js_string, self.field_name)
        if not exists:
            comma = "," if len(js_string.strip())>0 else ""
            self.before = js_string + comma
            self.before += self.field_name + ": ["
            self.contents = ",".join(self.must_have_fields)
            self.after += "]"
        if exists:
            content_list = [x for x in self.contents.strip().split(",") if x]
            contents = list(set(content_list).union(set(self.must_have_fields)))
            contents.sort()
            self.contents = ",".join(contents)

    def format_field(self) -> str:
        return self.before + self.contents + self.after

class FieldObj(BaseFieldObj):
    def __init__(self, field_name, must_have_field: BaseFieldObj):
        super().__init__(field_name)
        self.must_have_field = must_have_field

    def parse_string(self, js_string):
        exists, self.before, self.contents, self.after = split_on_field(js_string, self.field_name)
        if not exists:
            comma = "," if len(js_string.strip())>0 else ""
            self.before = js_string + comma
            self.before += self.field_name + ": {"
            self.must_have_field.parse_string("")
            self.contents = self.must_have_field.format_field()
            self.after += "}"
        if exists:
            self.must_have_field.parse_string(self.contents)

    def format_field(self) -> str:
        return self.before + self.must_have_field.format_field() + self.after

class HighLevelFieldObj(FieldObj):
    def parse_string(self, js_string):
        exists, self.before, self.contents, self.after = split_on_field(js_string, self.field_name)
        if not exists:
            self.before = js_string
            self.before += self.field_name + "= {"
            self.must_have_field.parse_string("")
            self.contents = self.must_have_field.format_field()
            self.after += "};"
        if exists:
            self.must_have_field.parse_string(self.contents)

    def format_field(self) -> str:
        return self.before + self.must_have_field.format_field() + self.after


def split_on_field(json_string, field_name):
    field_idx = json_string.find(field_name)
    if field_idx == -1:
        return False, json_string, "", ""
    before_field = json_string[:field_idx+len(field_name)]
    json_string = json_string[field_idx+len(field_name):]
    first_idx, last_idx = get_curly_brackets_idx(json_string)
    field_contents = json_string[first_idx:last_idx]
    before_field += json_string[:first_idx]
    after_field = json_string[last_idx:]
    return True, before_field, field_contents, after_field

def split_on_field_brackets(json_string, field_name):
    field_idx = json_string.find(field_name)
    if field_idx == -1:
        return False, "", json_string, ""
    before_field = json_string[:field_idx+len(field_name)]
    json_string = json_string[field_idx+len(field_name):]
    first_idx, last_idx = get_brackets_idx(json_string)
    field_contents = json_string[first_idx:last_idx]
    before_field += json_string[:first_idx]
    after_field = json_string[last_idx:]
    return True, before_field, field_contents, after_field

def field_exists(json_string, field_name):
    field_idx = json_string.find(field_name)
    if field_idx != -1:
        json_string_cut = json_string[field_idx:]
        return True, json_string_cut
    return False, json_string


def get_curly_brackets_idx(json_string):
    first_bracket_idx = json_string.find("{")
    json_string_new = json_string[first_bracket_idx:]
    last_bracket_index = match_curly_brackets(json_string_new)
    return first_bracket_idx+1, first_bracket_idx+last_bracket_index

def get_brackets_idx(json_string):
    first_bracket_idx = json_string.find("[")
    json_string_new = json_string[first_bracket_idx:]
    last_bracket_index = match_brackets(json_string_new)
    return first_bracket_idx+1, first_bracket_idx+last_bracket_index


# assumes brackets are balanced
def match_curly_brackets(bracketed_string):
    bracket_count = 0
    for i, c in enumerate(bracketed_string):
        if c == "{":
            bracket_count +=1
        elif c == "}" and bracket_count > 0:
            bracket_count -= 1
        if i != 0 and bracket_count == 0:
            return i

def match_brackets(bracketed_string):
    bracket_count = 0
    for i, c in enumerate(bracketed_string):
        if c == "[":
            bracket_count +=1
        elif c == "]" and bracket_count > 0:
            bracket_count -= 1
        if i != 0 and bracket_count == 0:
            return i
