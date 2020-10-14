![Python package](https://github.com/jvanasco/html5lib_to_markdown/workflows/Python%20package/badge.svg)

# html5lib_to_markdown

This package offers a way to convert HTML to the Markdown format.

This package is currently targeting a SUBSET of full HTML->Markdown conversion to address internal needs. More functionality will be added as needed. Pull requests are welcome.


## There are many packages that convert HTML to Markdown. Why create *another* package to do this task?

* Licensing. This package is available via the permissive MIT license. There are no GPL restrictions, which affect about a third of the other libraries that perform this task.

* Tests. This package ships with many tests to ensure things keep working as desired. Several existing libraries do not have tests or adequate test coverage.

* Customized Feature: Use HTML for certain elements instead of Markdown syntax.  Sometimes we WANT to use <a> and <img> tags, and not turn them into Markdown syntax.

* Core Implementation Detail. This package is implemented as a `htmllib5` "tree adapter", which means it can be layered into many htm5lib processing routines.  Other packages use `BeautifulSoup`, `lxml` or `HTMLParser`.  These other projects are all great, but require re-processing if you are already doing things with `html5lib`.

* Customized Feature: Clean up common html issues and make pretty Markdown.  This library doesn't just create Markdown, but optimized/pretty Markdown. This library attempts to optimize-away extra newlines and spaces, creating a concise and readable Markdown version.

* Customized Feature: ignore unwanted html tags and attributes.  

* Customized Feature: Idempotent when possible. This is more of a goal than a guarantee, but text that is processed through this library should not change if re-processed through this library whenever possible.  In other words, we're aiming for this:

```
as_markdown = to_markdown(html) == to_markdown(as_markdown) == to_markdown(to_markdown(html)) == to_markdown(to_markdown(as_markdown))
```

This can't be guaranteed in all situations because of how Markdown and HTML work, but it is a goal. This library should not add artifacts.

At a minimum, our goal is this
```
as_markdown = to_markdown(html) == to_markdown(to_html(as_markdown))
as_html = to_html(as_markdown) == to_html(to_markdown(as_html))
```

* Customized feature: A departure from the core Markdown specification was needed for a few elements:

	1. Render `img` tags, not Markdown format
	2. Render `a` tags, not Markdown format

* Customized feature: Python2 and Python3 compatibility. This shouldn't be a feature, but it is. Some excellent packages in this space stopped supporting Python2 already. This package aims to keep Python2 support around a bit longer than the official cutoff date, because legacy systems exist.


## Unsupported Features

Angled links are not currently supported, for example:

	<http://example.com>

They are not compatible with the html5lib parser, and trying to support them will require a lot of work.

## Pretty Markdown?

What is pretty Markdown?

* There is a max of 2 newlines (1 blank line) between elements.
* blank lines are dropped to the lowest allowable nesting of blockquotes or lists
* whitespace is shown via HTML rendering rules


## Other Libraries

The interface was inspired by the `bleach` user-input sanitization library, which relies on `html5lib`

If you just need a standard and pure "HTML to Markdown" convertor, I recommend the following libraries:

* `antimarkdown` http://github.com/Crossway/antimarkdown/
    * built on `lxml`
    * MIT license

* `markdownify` http://github.com/matthewwithanm/python-markdownify
    * built on `BeautifulSoup`
    * MIT license
 

## License & Copyright

This package is available under the MIT License.  The code and tests are: Copyright 2019 Jonathan Vanasco (jonathan@findmeon.com)

Additional code and tests are isolated in the tests_working directory (and soon to be tests), with copyright attributed to the antimarkdown and markdownify projects.  both are used under the MIT License and credited in the source


## Environment Variables
 
* `MD_DEBUG_TOKENS` - will use string representation for tokens (human readable!) instead of optimizing with ints
* `MD_DEBUG_STACKS` - will `print()` the tokens during 
* `MD_DEBUG_STACKS_SIMPLE` - will `print()` the tokens in a simplified form 


## TODO

See [TODO.txt](TODO.txt)

