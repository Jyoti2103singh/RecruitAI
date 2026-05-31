with open('templates/jobseeker/dashboard.html', encoding='utf-8') as f:
    content = f.read()

# Fix upload zone - remove the overlapping input and use direct click
old = '''    <div class="upload-zone" id="uploadZone">
        <input type="file" id="resumeFile" accept=".pdf,.docx,.doc,.txt">
        <div class="upload-icon">📂</div>
        <div class="upload-text">
          <strong>Click to upload</strong> or drag & drop<br>
          PDF, DOCX, DOC, TXT supported
        </div>
      </div>'''

new = '''    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('resumeFile').click()">
        <input type="file" id="resumeFile" accept=".pdf,.docx,.doc,.txt" style="display:none" onchange="fileSelected(this)">
        <div class="upload-icon">📂</div>
        <div class="upload-text" id="uploadText">
          <strong>Click to upload</strong> or drag & drop<br>
          PDF, DOCX, DOC, TXT supported
        </div>
      </div>'''

content = content.replace(old, new)

# Add fileSelected function before screenResume function
old = '  // ── SCREEN RESUME ──'
new = '''  // ── FILE SELECTED ──
  function fileSelected(input) {
    if (input.files && input.files[0]) {
      document.getElementById('uploadText').innerHTML = 
        '<strong style="color:var(--green)">✅ ' + input.files[0].name + '</strong><br><span style="font-size:0.75rem">Click Screen Resume to analyze</span>';
    }
  }

  // ── SCREEN RESUME ──'''

content = content.replace(old, new)

with open('templates/jobseeker/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')