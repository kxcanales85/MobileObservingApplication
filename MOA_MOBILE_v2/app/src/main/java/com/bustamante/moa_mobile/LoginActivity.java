package com.bustamante.moa_mobile;

import android.annotation.SuppressLint;
import android.content.Intent;
import com.bustamante.moa_mobile.Utilities.SharedPreference;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.os.AsyncTask;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.KeyEvent;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import java.io.IOException;
import okhttp3.Authenticator;
import okhttp3.Credentials;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.Route;

import static java.lang.System.*;
import static com.bustamante.moa_mobile.R.string.port_api;
import static com.bustamante.moa_mobile.R.string.url_host;

/**
 * A login screen that offers login via email/password.
 */
public class LoginActivity extends AppCompatActivity {

    private UserLoginTask mAuthTask = null;

    // UI references.
    private EditText mUsernameView;
    private EditText mPasswordView;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        getSupportActionBar().hide(); //código para ocultar la barra de arriba o actionbar
        //comprobamos si es que el usuario se ha registrado previamente o no
        boolean firstLogin = SharedPreference.getFirstLogin("FirstLogin", this);
        if(!firstLogin){
            //Comprobamos si es que el teléfono ya fue aceptado por el sistema
            boolean allowphone = SharedPreference.getBool("AllowPhone", this);
            //si es aceptado, entonces vamos al menú principal
            if(allowphone) {
                Intent intent = new Intent(this, ConnectionActivity.class);
                startActivity(intent);
                finish();
                //si no, vamos al activity para registrar el celular en el sistema
            } else {
                Intent intent = new Intent(this, AllowActivity.class);
                startActivity(intent);
                finish();
            }
        }

        // Set up the login form.
        mUsernameView = findViewById(R.id.username);
        mPasswordView = findViewById(R.id.password);
        mPasswordView.setOnEditorActionListener(new TextView.OnEditorActionListener() {
            @Override
            public boolean onEditorAction(TextView textView, int id, KeyEvent keyEvent) {
                if (id == EditorInfo.IME_ACTION_DONE || id == EditorInfo.IME_NULL) {
                    attemptLogin();
                    return true;
                }
                return false;
            }
        });

        Button mEmailSignInButton = findViewById(R.id.email_sign_in_button);
        mEmailSignInButton.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View view) {
                attemptLogin();
            }
        });
    }


    /**
     * Attempts to sign in or register the account specified by the login form.
     * If there are form errors (invalid email, missing fields, etc.), the
     * errors are presented and no actual login attempt is made.
     */
    private void attemptLogin() {
        if (mAuthTask != null) {
            return;
        }

        // Reset errors.
        mUsernameView.setError(null);
        mPasswordView.setError(null);

        // Store values at the time of the login attempt.
        String email = mUsernameView.getText().toString();
        String password = mPasswordView.getText().toString();

        boolean cancel = false;
        View focusView = null;

        // Check for a valid password, if the user entered one.
        if (!TextUtils.isEmpty(password) && !isPasswordValid(password)) {
            mPasswordView.setError(getString(R.string.error_invalid_password));
            focusView = mPasswordView;
            cancel = true;
        }

        // Check for a valid email address.
        if (TextUtils.isEmpty(email)) {
            mUsernameView.setError(getString(R.string.error_field_required));
            focusView = mUsernameView;
            cancel = true;
        }

        if (cancel) {
            // There was an error; don't attempt login and focus the first
            // form field with an error.
            focusView.requestFocus();
        } else {
            // Show a progress spinner, and kick off a background task to
            // perform the user login attempt.
            //showProgress(true);
            mAuthTask = new UserLoginTask(email, password);
            mAuthTask.execute((Void) null);
        }
    }

    private boolean isPasswordValid(String password) {
        //TODO: Replace this with your own logic
        return password.length() > 4;
    }

    /**
     * Represents an asynchronous login/registration task used to authenticate
     * the user.
     */
    @SuppressLint("StaticFieldLeak")
    public class UserLoginTask extends AsyncTask<Void, Void, Boolean> {

        private final String mUsername;
        private final String mPassword;

        UserLoginTask(String username, String password) {
            mUsername = username;
            mPassword = password;
        }

        @Override
        protected Boolean doInBackground(Void... params) {
            OkHttpClient client = new OkHttpClient.Builder()
                    .authenticator(new Authenticator() {
                        @Override
                        public Request authenticate(@NonNull Route route, @NonNull Response response) throws IOException {
                            if (response.request().header("Authorization") != null) {
                                return null; // Give up, we've already attempted to authenticate.
                            }
                            String credential = Credentials.basic(mUsername, mPassword);
                            return response.request().newBuilder()
                                    .header("Authorization", credential)
                                    .build();
                        }
                    })
                    .build();



            Request request = new Request.Builder()
                    .url(getResources().getString(url_host)+":"+getResources().getString(port_api)) //REPLACE URL
                    .build();

            try (Response response = client.newCall(request).execute()) {
                if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);

                out.println(response.body().string());
            } catch (IOException e) {
                e.printStackTrace();
            }
            return true;
        }

        @Override
        protected void onPostExecute(final Boolean success) {
            mAuthTask = null;

            if (success) {
                SharedPreference.setBoolean("FirstLogin", false, LoginActivity.this);
                SharedPreference.setString("Username", mUsername, LoginActivity.this);
                boolean allowphone = SharedPreference.getBool("AllowPhone", LoginActivity.this);
                //si el celular está aceptado, entonces podemos ir al menú principal
                if (allowphone){
                    Intent intent = new Intent(LoginActivity.this, ConnectionActivity.class);
                    startActivity(intent);
                    finish();
                }
                //si no, tenemos que redireccionar al activity de inscripción en el sistema
                else {
                    //Start activity for allow
                    Intent intent = new Intent(LoginActivity.this, AllowActivity.class);
                    startActivity(intent);
                    finish();
                }
            } else {
                mPasswordView.setError(getString(R.string.error_invalid_credentials));
                mPasswordView.requestFocus();
            }
        }

        @Override
        protected void onCancelled() {
            mAuthTask = null;
        }
    }
}

