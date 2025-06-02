from lxml import etree
import sys
import re

def fix_self_closing(xml: str) -> str:
    return re.sub(r'<(\w+)([^>]*)\s*/>', r'<\1\2></\1>', xml)

def apply_cdata_to_elements(root, tag_names):
    for elem in root.iter():
        if elem.tag in tag_names and elem.text and not isinstance(elem.text, etree.CDATA):
            elem.text = etree.CDATA(elem.text)

# 修正錯誤閉合標籤
def fix_misclosed_tags(xml: str) -> str:
    corrections = {
        'max-src-nodes': 'max-src-nodes',
        'max-src-conn': 'max-src-conn',
        'max-src-states': 'max-src-states',
    }
    for correct_tag in corrections:
        xml = re.sub(rf'<{correct_tag}></max>', rf'<{correct_tag}></{correct_tag}>', xml)
    return xml

def save_element_to_file(element, filename, cdata_tags):
    apply_cdata_to_elements(element, cdata_tags)
    xml_bytes = etree.tostring(
        element,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf-8'
    )
    xml_str = xml_bytes.decode('utf-8')
    fixed_str = fix_self_closing(xml_str)
    fixed_str = fix_misclosed_tags(fixed_str)
    with open(filename, 'wb') as f:
        f.write(fixed_str.encode('utf-8'))

def main(config_file, floating_rule_file, separator_file, output_file):
    # 讀入原始 config.xml
    config_tree = etree.parse(config_file)
    config_root = config_tree.getroot()

    # 讀入 floating rules
    floating_rules_tree = etree.parse(floating_rule_file)
    floating_rules_root = floating_rules_tree.getroot()

    # 將所有 floating rule 加入 config.xml 中
    # for rule in floating_rules_root:
    #     config_root.insert(0, rule)  # 插入最上方（你也可以調整順序）
    existing_rules = config_root.findall("rule")
    insert_index = config_root.index(existing_rules[0]) if existing_rules else 0
    for rule in floating_rules_root.findall("rule"):
        config_root.insert(insert_index, rule)
        insert_index += 1

    # 找到 separator
    separator_elem = config_root.find(".//separator")
    if separator_elem is not None:
        # 讀入 separator 中的 floatingrules
        sep_tree = etree.parse(separator_file)
        floating_sep = sep_tree.getroot()
        separator_elem.append(floating_sep)

    # 儲存結果
    save_element_to_file(config_root, output_file, {"descr", "text", "username"})

    print(f"✔ merge success! ouput file: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python merge_float.py config.xml floating_rules.xml floating_separators.xml output.xml")
        sys.exit(1)

    config_file = sys.argv[1]
    floating_rules_file = sys.argv[2]
    floating_separator_file = sys.argv[3]
    output_file = sys.argv[4]

    main(config_file, floating_rules_file, floating_separator_file, output_file)
