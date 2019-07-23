package com.bustamante.moa_mobile;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.AsyncTask;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.telephony.TelephonyManager;
import android.view.View;
import android.widget.Button;

import com.bustamante.moa_mobile.Utilities.SharedPreference;

import com.blikoon.qrcodescanner.QrCodeActivity;

import static com.bustamante.moa_mobile.R.string.error_msge_scan;
import static com.bustamante.moa_mobile.R.string.error_scan;
import static com.bustamante.moa_mobile.R.string.port_api;
import static com.bustamante.moa_mobile.R.string.url_host;


import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class AllowActivity extends AppCompatActivity {

    private static final int REQUEST_CODE_QR_SCAN = 101;
    OkHttpClient client = new OkHttpClient();
    private AllowPhoneTask mAuthTask = null;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_allow);
        Button button;
        button = findViewById(R.id.button_start_scan);
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(AllowActivity.this, QrCodeActivity.class);
                startActivityForResult(intent ,REQUEST_CODE_QR_SCAN);
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {

        if(resultCode != Activity.RESULT_OK)
        {
            if(data==null)
                return;
            //Getting the passed result
            String result = data.getStringExtra("com.blikoon.qrcodescanner.error_decoding_image");
            if( result!=null)
            {
                AlertDialog alertDialog = new AlertDialog.Builder(this).create();
                alertDialog.setTitle(getResources().getString(error_scan));
                alertDialog.setMessage(getResources().getString(error_msge_scan));
                alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                dialog.dismiss();
                            }
                        });
                alertDialog.show();
            }
            return;

        }
        if(requestCode == REQUEST_CODE_QR_SCAN)
        {
            if(data==null)
                return;
            //Getting the passed result
            String result = data.getStringExtra("com.blikoon.qrcodescanner.got_qr_scan_relult");

            mAuthTask = new AllowPhoneTask(result, getUniqueIMEIId(this));
            mAuthTask.execute((Void) null);
            /*if(checkAndValidatePhone(message[0], message[1])){
                SharedPreference.setBoolean("AllowPhone", true, this);
                //Start new activity
                Intent intent = new Intent(this, MainMenuActivity.class);
                startActivity(intent);
                finish();
            }
            else{
                AlertDialog alertDialog = new AlertDialog.Builder(this).create();
                alertDialog.setTitle(getResources().getString(error_scan));
                alertDialog.setMessage(getResources().getString(error_msge_scan));
                alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                dialog.dismiss();
                            }
                        });
                alertDialog.show();
                finish();

            }*/
        }
    }

    public static String getUniqueIMEIId(Context context) {
        try {
            TelephonyManager telephonyManager = (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
            if (ActivityCompat.checkSelfPermission(context, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
                // TODO: Consider calling
                //    ActivityCompat#requestPermissions
                // here to request the missing permissions, and then overriding
                //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
                //                                          int[] grantResults)
                // to handle the case where the user grants the permission. See the documentation
                // for ActivityCompat#requestPermissions for more details.
                return "";
            }
            String imei = telephonyManager.getDeviceId();
            if (imei != null && !imei.isEmpty()) {
                System.out.println("IMEI: "+imei);
                return imei;
            } else {
                return android.os.Build.SERIAL;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return "not_found";
    }

    public class AllowPhoneTask extends AsyncTask<Void, Void, String>{
        private final String mToken;
        private final String mImei;
        private String mResponse;

        AllowPhoneTask(String token, String imei){
            mToken = token;
            mImei = imei;
            mResponse = null;
        }

        @Override
        protected String doInBackground(Void... params) {
            String url = getResources().getString(url_host)+":"+getResources().getString(port_api)+"/doall/?token="+mToken+"&imei="+mImei;
            Request request = new Request.Builder()
                    .url(url)
                    .get()
                    .build();


            try {
                Response response = client.newCall(request).execute();
                System.out.println("response: "+response);
                if (!response.isSuccessful()) {
                    return null;
                }
                return response.body().string();
            } catch (Exception e) {
                e.printStackTrace();
                return null;
            }
        }

        @Override
        protected void onPostExecute(final String resp) {
            mAuthTask = null;
            //System.out.println("resp: "+resp);

            if (resp.equals("true")) {
                SharedPreference.setBoolean("AllowPhone", true, AllowActivity.this);
                //Start new activity
                Intent intent = new Intent(AllowActivity.this, ConnectionActivity.class);
                startActivity(intent);
                finish();
            }
            else{
                AlertDialog alertDialog = new AlertDialog.Builder(AllowActivity.this).create();
                alertDialog.setTitle(getResources().getString(error_scan));
                alertDialog.setMessage(getResources().getString(error_msge_scan));
                alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                dialog.dismiss();
                            }
                        });
                alertDialog.show();
            }
        }

        @Override
        protected void onCancelled() {
            mAuthTask = null;
        }
    }
}