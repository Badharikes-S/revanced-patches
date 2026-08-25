# ReVanced API v4 feed for Universal ReVanced Manager

This repository publishes a continuously updated **ReVanced API v4 JSON feed** for [Universal ReVanced Manager (URV)](https://github.com/Jman-Github/Universal-ReVanced-Manager). The feed is generated from the canonical upstream [ReVanced patches repository](https://gitlab.com/ReVanced/revanced-patches); this repository is only an automated distribution and build feed and does not claim ownership of the upstream patches.

## Import URL

Paste the following URL into URV's remote patch-bundle import dialog:

```text
https://raw.githubusercontent.com/Badharikes-S/revanced-patches/main/bundles/revanced-latest-patches-bundle.json
```

URV downloads the JSON metadata, follows its `download_url`, and then imports the referenced `.rvp` patch artifact. The JSON file is therefore a feed endpoint, not a substitute for the actual compiled patch bundle.

## What is published

The current feed is `bundles/revanced-latest-patches-bundle.json`. It contains the fields required by URV's current remote JSON asset model: `download_url`, `created_at`, `description`, `version`, and `page_url`. The compiled `.rvp` file is published as a versioned GitHub Release asset in this repository so that the raw JSON URL remains stable while each binary build remains addressable and replaceable.

The workflow validates the JSON syntax and required fields, confirms that the referenced artifact is a non-empty ZIP/JAR with a manifest and non-empty DEX entries, and refuses to publish an invalid build. The validation implementation is in [`scripts/validate_feed.py`](scripts/validate_feed.py).

## Update mechanism

[GitHub Actions](.github/workflows/update-revanced.yml) runs once per day at 03:17 UTC and can also be started manually with `workflow_dispatch`. Each run queries the upstream GitLab release API, selects the newest stable semantic-version release, checks out that exact tag, builds the official `.rvp` artifact with Java 17, generates the URV JSON feed, validates both outputs, and publishes a versioned release asset.

If the generated feed is byte-for-byte unchanged, no feed commit is created. When the upstream stable version changes, the workflow commits the new feed with `chore: update ReVanced patches`. A failed build or validation step stops the job before the existing feed is replaced.

This feed intentionally tracks **stable upstream releases**, not prereleases or arbitrary commits. That choice favors predictable URV compatibility. The exact upstream tag and commit are recorded in the feed description and in the workflow log for each successful update.

## Build and compatibility notes

The upstream ReVanced release workflow currently produces `.rvp` artifacts. The workflow uses the exact tagged ReVanced Gradle plugin source as an included build, which keeps the build reproducible without requiring a personal package token in this repository. The upstream patch source remains fetched directly from GitLab on every update.

The repository does not modify or permanently fork the upstream Git history. It stores only the stable JSON endpoint, workflow, validator, documentation, and GitHub Release assets. The source repository remains the canonical place for upstream code, release notes, and contribution guidance.

## Licensing

ReVanced Patches is licensed under the [GNU General Public License v3.0](https://gitlab.com/ReVanced/revanced-patches/-/blob/main/LICENSE). The license text is included in this repository. Any redistribution or modification of upstream-covered material must comply with GPLv3, including the applicable source-code and notice requirements. See the upstream license and repository for the authoritative terms.

## References

1. [ReVanced patches](https://gitlab.com/ReVanced/revanced-patches)
2. [Universal ReVanced Manager](https://github.com/Jman-Github/Universal-ReVanced-Manager)
3. [ReVanced patches Gradle plugin](https://github.com/ReVanced/revanced-patches-gradle-plugin)
4. [ReVanced Patches GPLv3 license](https://gitlab.com/ReVanced/revanced-patches/-/blob/main/LICENSE)
