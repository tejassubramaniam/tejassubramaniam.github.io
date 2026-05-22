# tejassubramaniam.com

Personal site and blog. Built with [Astro](https://astro.build), deployed via GitHub Pages.

## Local development

```bash
pnpm install        # or: npm install
pnpm dev            # serves at http://localhost:4321
pnpm build          # production build into ./dist
pnpm preview        # preview the production build locally
```

## Writing a new post

Drop a `.md` (or `.mdx`) file into `src/content/blog/`. Frontmatter schema:

```yaml
---
title: "Your post title"
description: "One-line description shown on the index."
pubDate: 2026-05-22
updatedDate: 2026-05-25      # optional
crosspost: https://...       # optional Substack URL — renders an "Also on Substack" note
draft: false                 # set true to hide
tags: ["tag-one", "tag-two"] # optional
---
```

LaTeX works out of the box via remark-math + rehype-katex:

```markdown
Inline: $\beta x + \varepsilon$

Display:
$$
y = X\beta + \varepsilon
$$
```

The file's name becomes the URL slug. `welcome.md` → `/blog/welcome/`.

## First-time deploy

1. Create a public GitHub repo (any name; the custom domain is what users see).
2. Push this folder to the `main` branch.
3. Repo Settings → Pages → set **Source** to **GitHub Actions**. The included workflow at `.github/workflows/deploy.yml` will build and deploy on every push to `main`.
4. Repo Settings → Pages → enter `tejassubramaniam.com` under **Custom domain**.
5. At your DNS registrar (where you bought the domain), replace existing records with:
   - Four `A` records on `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - One `CNAME` on `www` → `<your-github-username>.github.io`
6. Wait for the SSL certificate to provision (10 min to a few hours), then check **Enforce HTTPS** in Pages settings.
7. `public/CNAME` is already populated with `tejassubramaniam.com` — don't remove it; it's what tells GitHub Pages which domain to serve.

## Migrating from WordPress

1. WordPress admin → Tools → Export → All content → download the XML.
2. Convert it:
   ```bash
   npx wordpress-export-to-markdown
   ```
   Point it at the XML when prompted. It produces a folder of `.md` files with frontmatter.
3. Inspect each file. Common cleanup:
   - Image paths often need to be downloaded and placed under `public/images/`, with links updated.
   - HTML blocks that the exporter didn't convert (galleries, shortcodes) need manual rewriting.
   - Older posts may have entity-encoded characters (`&#8217;`) that should become real apostrophes.
4. Move the cleaned files into `src/content/blog/`.
5. Run `pnpm dev` and skim each post to make sure nothing's broken.

## Substack workflow

When publishing something that should go to both:
1. Write the post locally in markdown.
2. Commit and push — the site updates within ~2 minutes via GitHub Actions.
3. Paste the markdown into Substack's editor. Math may need re-entry — Substack's math support is weaker than KaTeX.
4. Add the Substack URL to the post's frontmatter as `crosspost: https://...` and push again. The post will display an "Also on Substack" note.

## Things to customize before going live

- `src/pages/index.astro` — replace the bio paragraphs with your actual links (Substack, Twitter, email, LinkedIn).
- `src/layouts/BaseLayout.astro` — update the site description.
- `astro.config.mjs` — the `site` URL is set; leave as is.
- `public/favicon.svg` — currently a plain "T" letterform; replace if you want something else.

## Adding pages beyond the blog

Just drop new `.astro` files into `src/pages/`. For example, `src/pages/research.astro` becomes `/research/`. Look at `src/pages/index.astro` for the pattern.
