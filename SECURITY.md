# Security

## Reporting a vulnerability

Report it privately through GitHub: on this repository's Security tab, choose "Report a vulnerability". Please do not open a public issue for it.

Say what you found, how to reproduce it, and which version or commit. If a file triggers it, attach a synthetic or anonymised one, never a real patient's scan.

## What matters most for Voxel

Voxel opens files from untrusted places: discs, downloads and email attachments. A file that makes Voxel crash, read outside its buffers, write anywhere, or run code is a security problem and will be treated as one.

## What Voxel does not do

Voxel has no network features, no account and no telemetry. It reads the files you open and writes only its own settings file and the pictures you export. The repository holds no secret.

## Medical use

Voxel is for review only and is not a certified medical device. A wrong image or a wrong measurement is a serious defect: report it as a normal issue, with a synthetic file that shows it.
