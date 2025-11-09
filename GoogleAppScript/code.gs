// ===========================
// ตั้งค่าพื้นฐาน
// ===========================
const SPREADSHEET_ID = '1qs10Pe8kuysAfTCu-Es_zrRJvujqEZKKRMygSojUKlc';
const LOGIN_SHEET_NAME = 'data';     // ชื่อชีตเก็บบัญชีผู้ใช้
const TRACKING_SHEET = 'Patient';


// ===========================
// ฟังก์ชันหลัก
// ===========================
function doGet(e) {
  let template;

  if (e && e.parameter.page) {
    const pageName = e.parameter.page.toLowerCase();
    if (pageName === 'admin') {
      template = HtmlService.createTemplateFromFile('patient');
    } else {
      template = HtmlService.createTemplateFromFile('index');
    }
  } else {
    // ถ้าไม่ส่งพารามิเตอร์ page → แสดงหน้า index
    template = HtmlService.createTemplateFromFile('index');
  }

  return template.evaluate()
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}


// ===========================
// ฟังก์ชันเสริม
// ===========================
function include(filename) {
  return HtmlService.createTemplateFromFile(filename).getContent();
}

function getWebAppUrl() {
  return ScriptApp.getService().getUrl();
}


// ===========================
// ✅ ฟังก์ชันตรวจสอบการล็อกอิน
// ===========================
function checkLogin(username, password, selectedRole) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(LOGIN_SHEET_NAME);
  if (!sheet) throw new Error(`ไม่พบชีตชื่อ '${LOGIN_SHEET_NAME}'`);

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) return { success: false, message: 'ไม่มีบัญชีผู้ใช้ในระบบ' };

  const headers = data[0].map(h => String(h).trim());
  const usernameCol = headers.indexOf('username');
  const passwordCol = headers.indexOf('password');
  const positionCol = headers.indexOf('ตำแหน่ง');
  const fullNameCol = headers.indexOf('ชื่อผู้ใช้');

  if (usernameCol === -1 || passwordCol === -1 || positionCol === -1)
    throw new Error('ไม่พบคอลัมน์ username, password, ตำแหน่ง ในชีต Login');

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const storedUsername = String(row[usernameCol] || '').trim();
    if (storedUsername === username) {
      const storedPassword = String(row[passwordCol] || '').trim();
      const storedRole = String(row[positionCol] || '').trim().toLowerCase();
      const storedFullName = fullNameCol !== -1 ? String(row[fullNameCol] || '').trim() : '';

      if (storedPassword !== password)
        return { success: false, field: 'password', message: 'รหัสผ่านไม่ถูกต้อง' };

      if (storedRole !== (selectedRole || '').toLowerCase())
        return { success: false, field: 'role', message: 'ประเภทผู้ใช้ไม่ตรงกับบัญชี' };

      return { success: true, position: storedRole, fullName: storedFullName };
    }
  }

  return { success: false, field: 'username', message: 'ไม่พบชื่อผู้ใช้' };
}

function getPatientData() {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(TRACKING_SHEET); // ใช้ค่าคงที่ด้านบน
    if (!sheet) throw new Error("❌ ไม่พบชีตชื่อ '" + TRACKING_SHEET + "'");

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      return [];
    }

    // 🔎 หาแถวหัวตาราง (ที่มีคำว่า date/day/time)
    let headerRowIndex = -1;
    let headers = [];

    for (let r = 0; r < data.length; r++) {
      const rowLower = data[r].map(v => String(v).trim().toLowerCase());
      if (
        rowLower.includes('date') ||
        rowLower.includes('day')  ||
        rowLower.includes('time')
      ) {
        headerRowIndex = r;
        headers = rowLower;
        break;
      }
    }

    if (headerRowIndex === -1) {
      throw new Error("❌ ไม่พบแถวหัวตารางที่มี 'Date/Day' หรือ 'Time' ในชีต " + TRACKING_SHEET);
    }

    // 🧩 หา index คอลัมน์วันที่/เวลา
    const dateIndex =
      headers.indexOf('date') !== -1
        ? headers.indexOf('date')
        : headers.indexOf('day');

    const timeIndex = headers.indexOf('time');

    if (dateIndex === -1 || timeIndex === -1) {
      throw new Error("❌ ไม่พบคอลัมน์ 'Date/Day' หรือ 'Time' ในชีต " + TRACKING_SHEET);
    }

    const result = [];

    // 📅 วนลูปอ่านข้อมูลตั้งแต่แถวถัดจากหัวตารางลงไป
    for (let i = headerRowIndex + 1; i < data.length; i++) {
      const dateValue = data[i][dateIndex];
      const timeValue = data[i][timeIndex];

      // ข้ามแถวว่าง
      if (!dateValue && !timeValue) continue;

      result.push({
        วันที่: formatDate(dateValue),
        เวลา: formatTime(timeValue)
      });
    }

    return result;
  } catch (err) {
    return [{ error: err.message }];
  }
}



// ✅ ฟังก์ชันจัดรูปแบบวันที่
function formatDate(value) {
  if (!value) return '';
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'dd/MM/yyyy');
  }
  return value;
}

// ✅ ฟังก์ชันจัดรูปแบบเวลา
function formatTime(value) {
  if (!value) return '';
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'HH:mm');
  }
  return value;
  
}
