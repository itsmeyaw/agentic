---
name: get-reviews
description: Obtain the reviews of an MR and produce a list of actionable items.
---

## Goal

Create actionable items from GitHub or GitLab issue trackers.

## Steps

1. Check for GitHub CLI or GitLab CLI availability based on the remote context. Ensure the CLI is authenticated. If required CLI doesn't exist, stop and ask user to install and authenticate.
2. Obtain information regarding GitHub PR or GitLab MR that need to be analyzed from the chat history. If no such information exists, inquiry user.
3. Get all comments informations from the remote using the CLI.
4. Convert all code-related review comments, ignoring normal conversations unrelated to code, into the following format:

  ```xml
  <review>
    <comments>
      <comment>Comment text</comment>
    </comments>
    <file path="referenced file path" lines="referenced line start - referenced line end">
      Snippet of the referenced file if exists
    </file>
  </review>
  ```
