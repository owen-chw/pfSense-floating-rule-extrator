from lxml import etree
from datetime import datetime
import sys
import os
import re

# 強制轉換 self-closing tags 為 open-close tags
def fix_self_closing(xml: str) -> str:
    return re.sub(r'<(\w+)([^>]*)\s*/>', r'<\1\2></\1>', xml)

def apply_cdata_to_elements(root, tag_names):
    for elem in root.iter():
        if elem.tag in tag_names and elem.text:
            elem.text = etree.CDATA(elem.text)

# 修正錯誤閉合標籤的函數
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



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("usuage: python3 extract_floating.py <input_config.xml> ")
        sys.exit(1)

    input_file = sys.argv[1]
    # output_floating_rules = "floating_rules.xml"
    # output_separators = "floating_separators.xml"
    # 建立以目前時間為名的資料夾
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"pfsense_extract_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_floating_rules = os.path.join(output_dir, "floating_rules.xml")
    output_separators = os.path.join(output_dir, "floating_separators.xml")

    if not os.path.exists(input_file):
        print(f"Error: can not find file {input_file}")
        sys.exit(1)

    # parse XML
    try:
        tree = etree.parse(input_file)
    except etree.XMLSyntaxError as e:
        print(f"XML parsing error：{e}")
        sys.exit(1)

    root = tree.getroot()
    filter_section = root

    if filter_section is None:
        print("error: cannot find <filter> block")
        sys.exit(1)

    # establish new root 
    floating_root = etree.Element("floating_rules")

    # 複製 floating="yes" 的 <rule>
    for rule in filter_section.findall('rule'):
        floating = rule.find('floating')
        if floating is not None and floating.text == 'yes':
            floating_root.append(rule)

    # --- 抽出 separator/floatingrules ---
    separator = root.find('.//separator')
    floating_separators = None
    if separator is not None:
        floating_separators = separator.find('floatingrules')
        if floating_separators is not None:
            # 深拷貝以避免原始結構損壞
            floating_separators = etree.ElementTree(floating_separators).getroot()

    # --- 寫入兩個檔案 ---
    save_element_to_file(floating_root, output_floating_rules, {"descr", "username", "statetype"})
    if floating_separators is not None:
        save_element_to_file(floating_separators, output_separators, {"text"})

    print(f"✔ Output saved in: {output_dir}")
    print(f"  ├─ {os.path.basename(output_floating_rules)}")
    print(f"  └─ {os.path.basename(output_separators)}")