import pandas as pd
from dataclasses import dataclass
from typing import List
from math import isnan
import markdown
import re
import yaml

@dataclass
class DataFile:
    url: str
    size: float
    size_unit: str
    file_type: str

@dataclass
class Dataset:
    title: str
    owner: str
    page_url: str
    date_created: str
    date_updated: str
    original_tags: List[str]
    manual_tags: List[str]
    license: str
    description: str
    num_records: int
    files: List[DataFile]

fulld = pd.read_csv("data/merged_output.csv", dtype=str, na_filter=False)
def ind(name):
    f = ['Unnamed: 0', 'Title', 'Owner', 'PageURL', 'AssetURL', 'DateCreated',
       'DateUpdated', 'FileSize', 'FileSizeUnit', 'FileType', 'NumRecords',
       'OriginalTags', 'ManualTags', 'License', 'Description', 'Source']
    return f.index(name)

def splittags(tags):
    if type(tags) == str:
        if tags == "":
            return []
        return tags.split(';')
    else:
        return []
def makeint(val):
    try:
        return int(val)
    except:
        pass
    try:
        return int(float(val))
    except:
        pass
    return None
    
data = {}
for r in fulld.values:
    id = str(r[ind('PageURL')]) + r[ind('Title')]
    if id not in data:
        ds = Dataset(
            title = r[ind('Title')],
            owner = r[ind('Owner')],
            page_url = r[ind('PageURL')],
            date_created = r[ind('DateCreated')],
            date_updated = r[ind('DateUpdated')].removesuffix(' 00:00:00.000'),
            original_tags = splittags(r[ind('OriginalTags')]),
            manual_tags = splittags(r[ind('ManualTags')]),
            license = r[ind('License')],
            description = str(r[ind('Description')]),
            num_records = makeint(r[ind('NumRecords')]),
            files = []
        )
        if ds.owner in ["South Ayrshire", "East Ayrshire"]:
            ds.owner += " Council"
        data[id] = ds
    data[id].files.append(
        DataFile(
            url = r[ind('AssetURL')],
            size = r[ind('FileSize')],
            size_unit = r[ind('FileSizeUnit')],
            file_type = r[ind('FileType')]
        ))

scotgov_data = pd.read_csv("scotgov-datasets.csv", dtype=str, na_filter=False)
for r in scotgov_data.values:
    ds = Dataset(
        title = r[0],
        original_tags = [r[1]],
        owner = r[2],
        description = r[3],
        date_created = r[4],
        date_updated = r[5],
        page_url = r[6],
        manual_tags = [],
        license = "OGL3",
        num_records = None,
        files = []
    )
    if ds.owner == "SEPA":
        ds.owner = "Scottish Environment Protection Agency"
    if ds.owner == "South Ayrshire":
        ds.owner = "South Ayrshire Council" # TODO: check if any of these actually supposed to be in the HSCP
    data[ds.page_url + ds.title] = ds


unknown_lics = []
def license_link(l):
    ogl = ["Open Government Licence 3.0 (United Kingdom)", "uk-ogl",
           "UK Open Government Licence (OGL)", "OGL3"]
    if l in ogl:
        return "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    if l == "Creative Commons Attribution Share-Alike 4.0":
        return "https://creativecommons.org/licenses/by-sa/4.0/"
    if l == "Creative Commons Attribution 4.0":
        return "https://creativecommons.org/licenses/by/4.0/"
    if l == "Open Data Commons Open Database License 1.0":
        return "https://opendatacommons.org/licenses/odbl/"
    
    if not l in unknown_lics:
        unknown_lics.append(l)
        print("Unknown license: ", l)
    return l

md = markdown.Markdown()

for k, ds in data.items():
    y = {'schema': 'default'}
    y['title'] = ds.title
    y['organization'] = ds.owner
    y['notes'] = markdown.markdown(ds.description)
    y['resources'] = [{'name': 'Description',
                       'url': ds.page_url,
                       'format': 'html'}] + [{'name': d.file_type,
                                              'url': d.url,
                                              'format': d.file_type} for d in ds.files]
    y['license'] = license_link(ds.license)
    y['category'] = ds.original_tags + ds.manual_tags
    y['maintainer'] = ds.owner
    y['date_created'] = ds.date_created
    y['date_updated'] = ds.date_updated
    y['records'] = ds.num_records
    fn = ds.owner + " - " + ds.title
    fn = re.sub(r'[^\w\s-]', '', fn).strip()
    # ^^ need something better for filnames...
    with open(f"_datasets/{fn}.md", "w") as f:
        f.write("---\n")
        f.write(yaml.dump(y))
        f.write("---\n")
