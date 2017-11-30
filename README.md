# Install

pip install -e git+ssh://#egg=tinypackager


# Config

### Deps:

/root.xml

```
project: test
destination:
  icons: Resources/icons/
  sources: _BUILD_SRC/%(project)s-%(name)s/
  resources: Resources/
packages:
  test:
    common: true
```

Some/package/package.xml

```
project: test
name: common
version: '1.0'
root:
  icons: Assets/
  resources: Resources/
data:
  icons:
  - igt_cf.png{.meta}
  icons screen=hd:
  - igt_cf.png{.meta}
  resources:
  - igt/igt_cf/**/*
  sources:
  - ./*.cs{.meta}
  - States/*.cs{.meta}
  - States/**/*.cs{.meta}
  - Binders/*.cs{.meta}
  - Shaders/*.shader{.meta}
  - Shaders/*.mat{.meta}
```

# Using

### Create package:

```
tinypackager create [package.yaml ...] --bucket=ZZZ --access_key XXX --secret_key YYY
```

### Install package:

```
tinypackager update --bucket=ZZZ --access_key XXX --secret_key YYY
```