#!/usr/bin/env node
// Release-Skript, unabhängig von GitHub (Regel „GitHub-Unabhängigkeit“, 07.11.2026).
// Legt zur aktuellen Version den Tag vX.Y.Z an und erstellt das Release mit dem
// Changelog-Abschnitt als Text – auf GitLab (glab bzw. GitLab-API) und auf GitHub (gh),
// je nachdem, was erreichbar ist. Läuft gleich am PC, in GitHub Actions und in GitLab CI.
//
//   node scripts/release.mjs              Release zur aktuellen Version anlegen (falls es fehlt)
//   node scripts/release.mjs --dry-run    nur anzeigen, was passieren würde
//   node scripts/release.mjs --all-missing   auch ältere Versionen nachtragen (nur mit vorhandenem Tag
//                                            oder Commit in der Kopfzeile „## X.Y.Z – … (`abc1234`)“)
// Optionen: --changelog <datei> (Standard CHANGELOG.md), --version <X.Y.Z>,
//           --version-from-changelog (oberste Version im Changelog statt package.json),
//           --title "<Name>" (Release-Titel = "<Name> X.Y.Z"; --title "" = nur die Nummer), --only gitlab|github,
//           --notes-file <datei> (fertiger Release-Text statt Changelog-Abschnitt, braucht --version)
// Kein Ziel erreichbar → Fehler. Ein Ziel nicht erreichbar → Hinweis, kein Fehler.
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const DRY = flag("--dry-run");
const ALL = flag("--all-missing");
const ONLY = opt("--only", "");
const CHANGELOG = opt("--changelog", "CHANGELOG.md");
const IN_GHA = process.env.GITHUB_ACTIONS === "true";
const IN_GLCI = !!process.env.GITLAB_CI;

const log = (...m) => console.log("[release]", ...m);
const run = (cmd, a, o = {}) => spawnSync(cmd, a, { encoding: "utf8", ...o });
const git = (...a) => execFileSync("git", ["-c", "safe.directory=*", ...a], { encoding: "utf8" }).trim();
const tryGit = (...a) => { try { return git(...a); } catch { return ""; } };

// ---------- Version und Changelog ----------
const NOTES_FILE_RAW = opt("--notes-file", ""); // „{v}“ wird durch die Version ersetzt
const text = NOTES_FILE_RAW ? "" : readFileSync(CHANGELOG, "utf8").replace(/\r\n/g, "\n");
const HEAD_RE = /^##\s+\[?v?(\d+\.\d+\.\d+)\]?(.*)$/;
const sections = [];
for (const line of text.split("\n")) {
  const m = line.match(HEAD_RE);
  if (m) sections.push({ v: m[1], head: m[2], body: [] });
  else if (/^##\s/.test(line)) sections.push({ v: null, head: line, body: [] });
  else if (sections.length) sections.at(-1).body.push(line);
}
const versioned = sections.filter((s) => s.v);
let current = opt("--version", "");
if (!current && flag("--version-from-changelog")) current = versioned[0]?.v;
if (!current && existsSync("package.json")) current = JSON.parse(readFileSync("package.json", "utf8")).version;
if (!current) { console.error("[release] Keine Version gefunden."); process.exit(1); }
const pkgName = existsSync("package.json") ? JSON.parse(readFileSync("package.json", "utf8")).name : "";
const TITLE = args.includes("--title") ? opt("--title", "") : (pkgName || "Release");
const NOTES_FILE = NOTES_FILE_RAW.replaceAll("{v}", current);
if (NOTES_FILE) versioned.unshift({ v: current, head: "", body: [readFileSync(NOTES_FILE, "utf8")] });
const notesOf = (s) => s.body.join("\n").trim() + "\n";
const shaOf = (s) => { const m = s.head.match(/`([0-9a-f]{7,40})`/); return m ? tryGit("rev-parse", `${m[1]}^{commit}`) : ""; };

const cur = versioned.find((s) => s.v === current);
if (!cur || !notesOf(cur).trim()) { console.error(`[release] Kein Eintrag für ${current} in ${CHANGELOG} – kein Release.`); process.exit(1); }
const todo = ALL ? [...versioned].reverse() : [cur];

// ---------- Ziele ----------
function remoteUrl(name) { return tryGit("remote", "get-url", name); }
function slugFrom(url, host) {
  const m = url.match(new RegExp(host.replace(".", "\\.") + "[:/](.+?)(?:\\.git)?$"));
  return m ? m[1] : "";
}
function glabBin() {
  const cands = [process.env.GLAB, process.env.LOCALAPPDATA && join(process.env.LOCALAPPDATA, "Programs", "glab", "glab.exe"), "glab"].filter(Boolean);
  for (const c of cands) { if (run(c, ["--version"]).status === 0) return c; }
  return "";
}
const ghSlug = process.env.GITHUB_REPOSITORY || slugFrom(remoteUrl("origin"), "github.com") || slugFrom(remoteUrl("github"), "github.com");
const glSlug = process.env.CI_PROJECT_PATH || slugFrom(remoteUrl("gitlab"), "gitlab.com")
  || slugFrom(tryGit("config", "--get-all", "remote.origin.pushurl").split("\n").find((u) => u.includes("gitlab.com")) || "", "gitlab.com");

const targets = [];
// GitLab
if (ONLY !== "github" && glSlug && !IN_GHA) {
  if (IN_GLCI && process.env.CI_JOB_TOKEN) targets.push(gitlabApiTarget());
  else { const g = glabBin(); if (g) targets.push(glabTarget(g)); else log("glab nicht gefunden – GitLab übersprungen."); }
}
// GitHub
if (ONLY !== "gitlab" && ghSlug && !IN_GLCI) {
  const ok = run("gh", ["api", `repos/${ghSlug}`, "--jq", ".full_name"]).status === 0;
  if (ok) targets.push(ghTarget());
  else log(`GitHub (${ghSlug}) nicht erreichbar – übersprungen. Später nachholen: Release-Skript erneut mit --only github starten.`);
}
if (!targets.length) { console.error("[release] Weder GitLab noch GitHub erreichbar."); process.exit(1); }

function ghTarget() {
  return {
    name: `GitHub ${ghSlug}`,
    exists: (tag) => run("gh", ["release", "view", tag, "--repo", ghSlug]).status === 0,
    create: (tag, title, file, sha, latest) => run("gh", ["release", "create", tag, "--repo", ghSlug, "--title", title, "--notes-file", file,
      ...(sha ? ["--target", sha] : []), `--latest=${latest}`], { stdio: "inherit" }).status === 0,
  };
}
function glabTarget(g) {
  return {
    name: `GitLab ${glSlug}`,
    exists: (tag) => run(g, ["release", "view", tag, "-R", glSlug]).status === 0,
    create: (tag, title, file, sha) => run(g, ["release", "create", tag, "-R", glSlug, "--name", title, "--notes-file", file,
      ...(sha ? ["--ref", sha] : [])], { stdio: "inherit" }).status === 0,
  };
}
function gitlabApiTarget() {
  const api = `${process.env.CI_API_V4_URL}/projects/${process.env.CI_PROJECT_ID}/releases`;
  const headers = { "JOB-TOKEN": process.env.CI_JOB_TOKEN, "Content-Type": "application/json" };
  return {
    name: `GitLab ${glSlug} (CI)`, async: true,
    exists: async (tag) => (await fetch(`${api}/${encodeURIComponent(tag)}`, { headers })).ok,
    create: async (tag, title, file, sha) => {
      const r = await fetch(api, { method: "POST", headers, body: JSON.stringify({ tag_name: tag, name: title, description: readFileSync(file, "utf8"), ref: sha || process.env.CI_COMMIT_SHA }) });
      if (!r.ok) console.error(`[release] GitLab-API ${r.status}: ${await r.text()}`);
      return r.ok;
    },
  };
}

// ---------- Ablauf ----------
const tmp = mkdtempSync(join(tmpdir(), "release-"));
const HEAD = tryGit("rev-parse", "HEAD") || process.env.CI_COMMIT_SHA || process.env.GITHUB_SHA;
let failed = 0;
for (const s of todo) {
  const tag = `v${s.v}`;
  const isCur = s.v === current;
  const localTag = tryGit("rev-parse", "-q", "--verify", `refs/tags/${tag}^{commit}`);
  const sha = localTag || shaOf(s) || (isCur ? HEAD : "");
  if (!sha) { if (ALL) continue; }
  const title = TITLE ? `${TITLE} ${s.v}` : s.v;
  const file = join(tmp, `${tag}.md`);
  writeFileSync(file, notesOf(s));
  // Tag lokal anlegen und hochladen (nicht in CI – dort legt die Release-API den Tag an)
  if (!IN_GHA && !IN_GLCI && !localTag) {
    if (DRY) log(`würde Tag ${tag} auf ${sha.slice(0, 7)} anlegen und pushen`);
    else {
      git("tag", "-a", tag, sha, "-m", title);
      for (const r of ["gitlab", "origin"]) {
        if (!remoteUrl(r)) continue;
        const p = run("git", ["push", r, `refs/tags/${tag}`], { stdio: "inherit" });
        if (p.status !== 0) log(`Tag-Push an ${r} fehlgeschlagen (GitHub gesperrt? dann erwartet).`);
      }
    }
  }
  for (const t of targets) {
    if (await t.exists(tag)) { if (isCur) log(`${t.name}: ${tag} gibt es schon.`); continue; }
    if (DRY) { log(`${t.name}: würde Release „${title}“ anlegen (${sha.slice(0, 7)})`); continue; }
    const ok = await t.create(tag, title, file, sha, isCur);
    log(`${t.name}: ${ok ? "angelegt" : "FEHLGESCHLAGEN"} – ${tag}`);
    if (!ok && isCur) failed++;
  }
}
process.exit(failed ? 1 : 0);
