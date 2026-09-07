-- Deterministic structural adapter for Report A.
-- The Markdown manuscript remains the sole editable scientific-prose authority.

local stringify = pandoc.utils.stringify

local function strip_numeric_prefix(inlines)
  if #inlines == 0 then
    return inlines
  end
  local first = inlines[1]
  if first.t == "Str" and first.text:match("^%d+[%.%d]*%.?$") then
    table.remove(inlines, 1)
    if #inlines > 0 and inlines[1].t == "Space" then
      table.remove(inlines, 1)
    end
  end
  return inlines
end

local function appendix_title(label)
  local _, _, title = label:find("^Appendix%s+[A-Z]%.?%s*(.*)$")
  return title
end

function Pandoc(doc)
  local output = {}
  local started = false
  local appendix_started = false

  for _, block in ipairs(doc.blocks) do
    if not started then
      if block.t == "Header" and block.level == 2 and stringify(block.content) == "Abstract" then
        started = true
        block.level = 1
        block.identifier = "abstract"
        table.insert(block.classes, "unnumbered")
        table.insert(output, block)
      end
    else
      if block.t == "Header" then
        local label = stringify(block.content)
        local app_title = appendix_title(label)
        if app_title ~= nil then
          if not appendix_started then
            table.insert(output, pandoc.RawBlock("latex", "\\appendix"))
            appendix_started = true
          end
          block.level = 1
          if app_title ~= "" then
            block.content = {pandoc.Str(app_title)}
          end
        elseif label == "References" then
          block.level = 1
          block.identifier = "references"
          table.insert(block.classes, "unnumbered")
        elseif appendix_started then
          -- This edition already uses natural Markdown appendix levels.
          -- B.1/D.1 prefixes are supplied by LaTeX subsection numbering.
          if #block.content > 0 and block.content[1].t == "Str"
              and block.content[1].text:match("^[A-Z]%.%d+[%.%d]*%.?$") then
            table.remove(block.content, 1)
            if #block.content > 0 and block.content[1].t == "Space" then
              table.remove(block.content, 1)
            end
          end
        else
          if block.level >= 2 then
            block.level = block.level - 1
          end
          block.content = strip_numeric_prefix(block.content)
        end
      end
      table.insert(output, block)
    end
  end

  assert(started, "Report A assembly could not locate the level-2 Abstract heading")
  assert(appendix_started, "Report A assembly could not locate Appendix A")
  doc.blocks = output
  return doc
end

-- Formatting only: permit long source paths/hashes/IDs to break, without
-- changing their literal content. xurl supplies safe break opportunities.
function Code(code)
  -- Page 10 review found an inserted line-end hyphen inside this literal.
  if code.text == "RATIO_UNIDENTIFIED" then
    return pandoc.RawInline("latex", "\\mbox{\\texttt{RATIO\\_UNIDENTIFIED}}")
  end
  if #code.text > 24 then
    assert(not code.text:find("[{}\\]"), "unsupported literal in code wrapper")
    return pandoc.RawInline("latex", "{\\ttfamily\\nolinkurl{" .. code.text .. "}}")
  end
end
