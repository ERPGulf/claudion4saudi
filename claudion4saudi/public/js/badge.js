frappe.ui.form.on('Advance Sales Invoice', {
  refresh(frm) {
      console.log("Form refreshed!");
      frm.set_df_property('custom_zatca_status_notification', 'options', ' ');

      if (frm.doc.custom_zatca_full_response) {
          try {
              console.log("custom_zatca_full_response found:", frm.doc.custom_zatca_full_response);
              let ztcaresponse = frm.doc.custom_zatca_full_response;

      // ✅ Check if the response starts with "Error"
              if (ztcaresponse.trim().toUpperCase().startsWith("ERROR")) {
                  console.log("Error detected in ZATCA response. Displaying Failed badge.");
                  let badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-failed.png" alt="Failed" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';
                  frm.set_df_property('custom_zatca_status_notification', 'options', badgeHtml);
                  frm.refresh_field('custom_zatca_status_notification');
                  return; // Exit since it's an error
              }
          
              let zatcaResponse = JSON.parse(ztcaresponse.match(/ZATCA Response: ({.*})/)[1]);

              const validationResults = zatcaResponse.validationResults || {};
              const status = validationResults.status; // PASS/WARNINGAILED

              // Use reporting status from custom_zatca_status field
              const reportingStatus = frm.doc.custom_zatca_status || ''; // Cleared/Reported
              const warnings = validationResults.warningMessages || [];

              console.log("Validation Status:", status);
              console.log("Reporting Status (from custom_zatca_status):", reportingStatus);
              console.log("Warnings:", warnings);

              let badgeHtml = ''; // Placeholder for image HTML

              // 🟢 PASS Conditions
              if (status === 'PASS') {
                  if (reportingStatus === 'CLEARED') {
                      console.log('PASS - Cleared');
                      badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-cleared.png" alt="Cleared" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';

                  } else if (reportingStatus === 'REPORTED') {
                      console.log('PASS - Reported');
                      badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-reported.png" alt="Reported" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';
                  }
              }

              // 🟡 WARNING Conditions
              else if (status === 'WARNING') {
                  if (reportingStatus === 'CLEARED') {
                      console.log('WARNING - Cleared with Warning');
                      badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-cleared-warning.png" alt="Cleared with Warning" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';
                  } else if (reportingStatus === 'REPORTED') {
                      console.log('WARNING - Reported with Warning');
                      badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-reported-warning.png" alt="Reported with Warning" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';
                  }
              }

              // 🔴 FAILED Condition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
              else {
                  console.log('FAILED');
                  badgeHtml = '<div class="zatca-badge-container"><img src="/assets/zatca_erpgulf/js/badges/zatca-failed.png" alt="Failed" class="zatca-badge" width="110" height="36" style="margin-top: -5px; margin-left: 215px;"></div>';
              }

              // Set Badge or Clear if None
              if (badgeHtml) {
                  frm.set_df_property('custom_zatca_status_notification', 'options', badgeHtml);
              } else {
                  console.log('No matching condition. Clearing badge.');
                  frm.set_df_property('custom_zatca_status_notification', 'options', '');
              }

          } catch (error) {
              console.error('Error parsing custom_zatca_full_response:', error);
              frm.set_df_property('custom_zatca_status_notification', 'options', '');
          }
      } else {
          console.log('No custom_zatca_full_response found.');
          frm.set_df_property('custom_zatca_status_notification', 'options', ' ');
      }

      frm.refresh_field('custom_zatca_status_notification');  
  
      
  }
});
