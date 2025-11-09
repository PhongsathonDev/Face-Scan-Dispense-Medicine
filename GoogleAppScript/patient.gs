// ถ้าในชีตมีคอลัมน์ชื่อ "Timestamp" จะให้ใส่เวลาให้อัตโนมัติ (วัน+เวลา)
const TIMESTAMP_HEADER = "Timestamp";

// เพิ่มหัวคอลัมน์สำหรับวันและเวลาแยกกัน
const DATE_HEADER = "Date";   // ชื่อหัวคอลัมน์สำหรับ "วัน"
const TIME_HEADER = "Time";   // ชื่อหัวคอลัมน์สำหรับ "เวลา"

// ฟังก์ชันหา "แถวว่างตัวแรก" จากด้านบน โดยดูจากคอลัมน์หลัก (เช่น Date หรือ Timestamp)
function getFirstEmptyRow(sheet, baseColIndex1Based) {
  var headerRow = 1;
  var lastRow = sheet.getLastRow();

  // ถ้ายังมีแค่แถวหัวตาราง ก็เริ่มที่แถว 2 เลย
  if (lastRow <= headerRow) {
    return headerRow + 1;
  }

  var startRow = headerRow + 1;
  var numRows = lastRow - headerRow;

  var range = sheet.getRange(startRow, baseColIndex1Based, numRows, 1);
  var values = range.getValues(); // [ [value], [value], ... ]

  for (var i = 0; i < values.length; i++) {
    if (!values[i][0]) {
      // ถ้าเจอเซลล์ว่าง แถวนี้คือแถวแรกที่ว่าง
      return startRow + i;
    }
  }

  // ถ้าไม่มีแถวว่างตรงกลาง ให้เขียนต่อท้าย
  return lastRow + 1;
}

function doPost(e) {
  try {
    if (!e.postData || !e.postData.contents) {
      throw new Error("No POST data");
    }

    // อ่าน JSON จาก Python
    var payload = JSON.parse(e.postData.contents);

    // อ่านชื่อชีตปลายทางจาก JSON
    // ถ้าไม่ส่ง sheet มา จะใช้ "Sheet1" เป็นค่า default
    var sheetName = payload.sheet || "Sheet1";
    var rowDataObj = payload.data;

    if (!rowDataObj) {
      throw new Error("No 'data' field in JSON payload");
    }

    // ใช้ Spreadsheet ที่ script ผูกอยู่ (ไม่ใช้ openById แล้ว)
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) {
      throw new Error("No active spreadsheet. Make sure this script is bound to a Google Sheet.");
    }

    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      throw new Error("Sheet not found: " + sheetName);
    }

    // อ่านหัวตารางจากแถวที่ 1
    var headerRow = 1;
    var lastCol = sheet.getLastColumn();
    if (lastCol === 0) {
      throw new Error("No header row found in sheet: " + sheetName);
    }

    var headerValues = sheet
      .getRange(headerRow, 1, 1, lastCol)
      .getValues()[0];  // array ของชื่อหัวแต่ละคอลัมน์

    // สร้าง map: "ชื่อหัว" → index (0-based)
    var headerIndexMap = {};  // { "HeaderName": index }
    for (var i = 0; i < headerValues.length; i++) {
      var h = headerValues[i];
      if (h) {
        headerIndexMap[String(h).trim()] = i; // index เริ่ม 0
      }
    }

    // เตรียม array สำหรับแถวใหม่
    var newRow = new Array(headerValues.length).fill("");

    // ใส่ค่าจาก payload.data ตามชื่อหัว
    for (var key in rowDataObj) {
      if (!rowDataObj.hasOwnProperty(key)) continue;

      var headerName = String(key).trim();
      if (headerIndexMap.hasOwnProperty(headerName)) {
        var colIndex = headerIndexMap[headerName]; // 0-based
        newRow[colIndex] = rowDataObj[key];
      }
      // ถ้าหัวไม่เจอในชีต ก็จะข้ามไม่เขียน
    }

    // ---- ใส่วัน/เวลาอัตโนมัติ ----
    var now = new Date();

    // ถ้ามีหัวชื่อ "Timestamp" → ใส่วัน+เวลา (Date object ปกติ)
    if (headerIndexMap.hasOwnProperty(TIMESTAMP_HEADER)) {
      var tsColIndex = headerIndexMap[TIMESTAMP_HEADER];
      newRow[tsColIndex] = now;
    }

    // ถ้ามีหัวชื่อ "Date" ให้ใส่เฉพาะ "วัน" (ตัดเวลาออก)
    if (headerIndexMap.hasOwnProperty(DATE_HEADER)) {
      var dateColIndex = headerIndexMap[DATE_HEADER];
      var onlyDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      newRow[dateColIndex] = onlyDate;
    }

    // ถ้ามีหัวชื่อ "Time" ให้ใส่เฉพาะเวลา (เก็บเป็นข้อความล้วน ๆ)
    if (headerIndexMap.hasOwnProperty(TIME_HEADER)) {
      var timeColIndex = headerIndexMap[TIME_HEADER];

      // แปลงเวลาเป็นสตริง
      var timeStr = Utilities.formatDate(now, Session.getScriptTimeZone(), "HH:mm:ss");

      // ใส่ ' นำหน้า บังคับให้ Google Sheet เก็บเป็น "ข้อความ"
      newRow[timeColIndex] = "'" + timeStr;
    }

    // ---- หาแถวที่จะเขียน (แถวว่างตัวแรก) ----
    var baseColIndex1Based = 1; // default ใช้คอลัมน์ A

    if (headerIndexMap.hasOwnProperty(DATE_HEADER)) {
      // ใช้คอลัมน์ Date เป็นคอลัมน์หลักในการเช็กแถวว่าง
      baseColIndex1Based = headerIndexMap[DATE_HEADER] + 1; // แปลงเป็น 1-based
    } else if (headerIndexMap.hasOwnProperty(TIMESTAMP_HEADER)) {
      // ถ้าไม่มี Date แต่มี Timestamp ให้ใช้ Timestamp แทน
      baseColIndex1Based = headerIndexMap[TIMESTAMP_HEADER] + 1;
    }

    var nextRow = getFirstEmptyRow(sheet, baseColIndex1Based);

    // เขียนค่า newRow ลงไป
    sheet.getRange(nextRow, 1, 1, newRow.length).setValues([newRow]);

    var result = {
      status: "ok",
      sheet: sheetName,
      row: nextRow
    };

    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    var errorResult = {
      status: "error",
      message: err.message,
      stack: err.stack
    };
    return ContentService
      .createTextOutput(JSON.stringify(errorResult))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
