Git Graphviz is a tool to generate a Graph of the repository using Graphviz. This tool was heavy inspired by [GitVersionTree](https://github.com/crc8/GitVersionTree).

# Install

Clone this repository and copy ```git-graphviz.py``` to you PATH and remove the extension ```py```. A one line command install:

```
sudo wget https://github.com/demitriusbelai/git-graphviz/raw/master/git-graphviz.py -O /usr/local/bin/git-graphviz
```

# Dependencies

Need to install Graphviz to generate SVG file. Or you can comment out the last line in the code to use another visualization tool.

# Use

Just run:

```
git graphviz
```

It will generate ```$GIT_DIR/graphviz.gv``` and ```$GIT_DIR/graphviz.svg```. Usualy ```$GIT_DIR``` is ```.git```.

You can pass arguments to ```git-log```:

```
git graphviz -- --branches=fix*
```

