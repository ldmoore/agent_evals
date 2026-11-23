Harden `extract_archive` in `/app/safe_extract.py`. Keep its public signature.

`extract_archive` must extract only regular files and directories below
`destination`; it must never call `ZipFile.extract` or `extractall`.

Before creating, modifying, or deleting anything in `destination`, validate
**every** archive member. If any member is invalid, raise `ValueError` whose
message includes that member's original name, and leave the destination exactly
as it was before the call.

Reject a member when its name is unsafe on either POSIX or Windows: absolute or
drive-qualified paths, UNC paths, or any name with a `..` component. Treat both
`/` and `\` as separators for validation. Reject non-regular, non-directory ZIP
entries, including symbolic links.

For valid archives, preserve the archive member order in the returned list of
written paths. Existing destination files must not be overwritten; raise
`ValueError` containing the conflicting member name instead.

Run the available tests before finishing.
