[app]
title = Gafori Studio
package.name = gaforistudio
package.domain = com.gafori
source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,ttf
version = 1.0.0
requirements = python3,kivy,pillow,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0

# Android build settings
android.api = 33
android.minapi = 23
android.ndk = 25b
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
