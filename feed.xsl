<?xml version="1.0" encoding="UTF-8"?>
<!-- Makes the RSS feeds render as a readable page when opened in a browser,
     instead of showing raw XML. News readers ignore this entirely. -->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title><xsl:value-of select="/rss/channel/title"/></title>
<style>
  :root { color-scheme: light; --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b;
    --ink-2:#52514e; --muted:#898781; --grid:#e1e0d9; --blue:#2a78d6; }
  @media (prefers-color-scheme: dark) { :root {
    --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink-2:#c3c2b7;
    --muted:#898781; --grid:#2c2c2a; --blue:#3987e5; } }
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--page);
    color:var(--ink);font-size:15px;line-height:1.5;padding:26px 20px 60px}
  .wrap{max-width:760px;margin:0 auto}
  h1{font-size:22px;letter-spacing:-0.4px;margin-bottom:4px}
  .sub{color:var(--ink-2);font-size:14px;margin-bottom:16px}
  .note{background:var(--surface);border:1px solid var(--grid);border-left:4px solid var(--blue);
    border-radius:10px;padding:14px 16px;margin-bottom:22px;font-size:13.5px;color:var(--ink-2)}
  .note b{color:var(--ink)}
  .note a{color:inherit}
  .item{background:var(--surface);border:1px solid var(--grid);border-radius:10px;
    padding:14px 16px;margin-bottom:11px}
  .item h2{font-size:16px;line-height:1.35;margin-bottom:5px}
  .item h2 a{color:inherit;text-decoration:none}
  .item h2 a:hover{text-decoration:underline}
  .meta{font-size:11.5px;color:var(--muted);text-transform:uppercase;
    letter-spacing:.4px;font-weight:700;margin-bottom:6px}
  .desc{font-size:13.5px;color:var(--ink-2)}
  .back{display:inline-block;margin-bottom:18px;font-size:13px;font-weight:600;color:var(--ink-2)}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="./">← Back to Lede</a>
  <h1><xsl:value-of select="/rss/channel/title"/></h1>
  <div class="sub"><xsl:value-of select="/rss/channel/description"/></div>

  <div class="note">
    <b>This page is a feed.</b> Paste this page's address into a news reader
    (NetNewsWire, Feedly, Inoreader, Reeder…) and new stories arrive automatically —
    no account, no algorithm, no tracking. If you don't use a reader, just
    <a href="./">browse Lede normally</a> instead; nothing here is missing from the site.
  </div>

  <xsl:for-each select="/rss/channel/item">
    <div class="item">
      <div class="meta">
        <xsl:value-of select="category"/>
      </div>
      <h2><a href="{link}"><xsl:value-of select="title"/></a></h2>
      <div class="desc"><xsl:value-of select="description" disable-output-escaping="yes"/></div>
    </div>
  </xsl:for-each>
</div>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
