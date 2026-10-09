"""Make the increment's Maven projects independently buildable; no report edits."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
ns = 'http://maven.apache.org/POM/4.0.0'
ET.register_namespace('', ns)
def tag(name): return f'{{{ns}}}{name}'
for name in ('coldtrace-shared', 'coldtrace-monitoring-service', 'coldtrace-api-gateway'):
    path = root / 'sprint1' / name / 'pom.xml'
    tree = ET.parse(path)
    project = tree.getroot()
    parent = project.find(tag('parent'))
    parent.clear()
    for key, value in [('groupId','org.springframework.boot'), ('artifactId','spring-boot-starter-parent'), ('version','3.3.13'), ('relativePath','')]:
        ET.SubElement(parent,tag(key)).text=value
    if project.find(tag('groupId')) is None:
        project.insert(2,ET.Element(tag('groupId')))
        project.find(tag('groupId')).text='com.acme.coldtrace'
    if project.find(tag('version')) is None:
        ET.SubElement(project,tag('version')).text='0.1.0-SNAPSHOT'
    properties = project.find(tag('properties'))
    if properties is None: properties=ET.SubElement(project,tag('properties'))
    if properties.find(tag('java.version')) is None: ET.SubElement(properties,tag('java.version')).text='21'
    deps=project.find(tag('dependencies'))
    for dependency in list(deps):
        if dependency.findtext(tag('artifactId')) == 'lombok': deps.remove(dependency)
    if name == 'coldtrace-api-gateway' and not any(d.findtext(tag('artifactId'))=='coldtrace-shared' for d in deps):
        dep=ET.SubElement(deps,tag('dependency'))
        for key,value in [('groupId','com.acme.coldtrace'),('artifactId','coldtrace-shared'),('version','0.1.0-SNAPSHOT')]: ET.SubElement(dep,tag(key)).text=value
    ET.indent(tree, space='  ')
    tree.write(path,encoding='utf-8',xml_declaration=True)
