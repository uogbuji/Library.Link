# Library.Link
Tools for processing data from the Library.Link project

Uche Ogbuji < uche@ogbuji.net >

# Install

Requires:

* Python 3.4+
* `amara3-xml` package
* `html5lib` package
* `pytest` (for running the test suite)

For the latter 3 you can do:

```
pip install pytest amara3-xml html5lib
```

# Use

## parse_rdfa

Command Tool to parse RDFa 1.1 Lite (from the Library.Link pages or other HTML). Example:

```
parse_rdfa --rdfttl=foo.ttl "http://link.houstonlibrary.org/portal/Half-of-a-yellow-sun-Chimamanda-Ngozi/n7KqqbZFJuM/"
```

Which outputs RDF Turtle to a file `foo.ttl`



# Technical background on the Library.Link network

Network-level resources

Take an ID 2_8BKlrtCTI

There is 

* http://library.link/resource/2_8BKlrtCTI/ : HTML rendered from feed.json



The top-level @type in brief.json & feed.json is preferredType

http://library.link/resource/2_8BKlrtCTI/brief.json





