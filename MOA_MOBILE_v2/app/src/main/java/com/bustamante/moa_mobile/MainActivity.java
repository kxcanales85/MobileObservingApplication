package com.bustamante.moa_mobile;

import android.Manifest;
import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.AsyncTask;
import android.os.Build;
import android.os.SystemClock;
import android.support.annotation.Nullable;
import android.support.v4.app.ActivityCompat;
import android.support.v4.app.FragmentActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.maps.CameraUpdate;
import com.google.android.gms.maps.CameraUpdateFactory;
import com.google.android.gms.maps.GoogleMap;
import com.google.android.gms.maps.OnMapReadyCallback;
import com.google.android.gms.maps.SupportMapFragment;
import com.google.android.gms.maps.model.BitmapDescriptorFactory;
import com.google.android.gms.maps.model.LatLng;
import com.google.android.gms.maps.model.Marker;
import com.google.android.gms.maps.model.MarkerOptions;

import java.io.IOException;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import dji.common.flightcontroller.FlightControllerState;
import dji.common.mission.waypoint.Waypoint;
import dji.common.mission.waypoint.WaypointMission;
import dji.common.mission.waypoint.WaypointMissionDownloadEvent;
import dji.common.mission.waypoint.WaypointMissionExecutionEvent;
import dji.common.mission.waypoint.WaypointMissionFinishedAction;
import dji.common.mission.waypoint.WaypointMissionFlightPathMode;
import dji.common.mission.waypoint.WaypointMissionHeadingMode;
import dji.common.mission.waypoint.WaypointMissionUploadEvent;
import dji.common.useraccount.UserAccountState;
import dji.common.util.CommonCallbacks;
import dji.sdk.base.BaseProduct;
import dji.sdk.flightcontroller.FlightController;
import dji.common.error.DJIError;
import dji.sdk.mission.waypoint.WaypointMissionOperator;
import dji.sdk.mission.waypoint.WaypointMissionOperatorListener;
import dji.sdk.products.Aircraft;
import dji.sdk.sdkmanager.DJISDKManager;
import dji.sdk.useraccount.UserAccountManager;

import io.socket.client.IO;
import io.socket.client.Socket;
import io.socket.emitter.Emitter;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import static com.bustamante.moa_mobile.R.string.no_mission_active;
import static com.bustamante.moa_mobile.R.string.no_mission_active_tittle;
import static com.bustamante.moa_mobile.R.string.port_api;
import static com.bustamante.moa_mobile.R.string.port_socket;
import static com.bustamante.moa_mobile.R.string.url_host;
import com.bustamante.moa_mobile.Utilities.SharedPreference;

import org.json.JSONException;
import org.json.JSONObject;

public class MainActivity extends FragmentActivity implements View.OnClickListener, GoogleMap.OnMapClickListener, OnMapReadyCallback {

    private static final String TAG = MainActivity.class.getName();

    private Socket mSocket;
    private Boolean isConnected = false;
    private MissionTask mAuthTask = null;

    private GoogleMap gMap;

    //private Button locate, add, clear;
    //private Button config, upload, start, stop;
    private TextView incomingMsg;
    private Button cancelMission;

    private boolean isAdd = false;

    private double droneLocationLat = 181, droneLocationLng = 181;
    private final Map<Integer, Marker> mMarkers = new ConcurrentHashMap<Integer, Marker>();
    private Marker droneMarker = null;

    private float altitude = 100.0f;
    private float mSpeed = 10.0f;

    private List<Waypoint> waypointList = new ArrayList<>();

    public static WaypointMission.Builder waypointMissionBuilder;
    private FlightController mFlightController;
    private WaypointMissionOperator instance;
    private WaypointMissionFinishedAction mFinishedAction = WaypointMissionFinishedAction.NO_ACTION;
    private WaypointMissionHeadingMode mHeadingMode = WaypointMissionHeadingMode.AUTO;

    private boolean waitingResponse = false;

    @Override
    protected void onResume(){
        super.onResume();
        initFlightController();
    }

    @Override
    protected void onPause(){
        super.onPause();
    }

    @Override
    protected void onDestroy(){
        unregisterReceiver(mReceiver);
        removeListener();
        super.onDestroy();
    }

    /**
     * @Description : RETURN Button RESPONSE FUNCTION
     */
    public void onReturn(View view){
        Log.d(TAG, "onReturn");
        this.finish();
    }

    private void setResultToToast(final String string){
        MainActivity.this.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(MainActivity.this, string, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void initUI() {
        incomingMsg = findViewById(R.id.ConnectStatusTextView);

        cancelMission = findViewById(R.id.cancelMission);
        cancelMission.setOnClickListener(this);

        /*locate = (Button) findViewById(R.id.locate);
        add = (Button) findViewById(R.id.add);
        clear = (Button) findViewById(R.id.clear);
        config = (Button) findViewById(R.id.config);
        upload = (Button) findViewById(R.id.upload);
        start = (Button) findViewById(R.id.start);
        stop = (Button) findViewById(R.id.stop);

        locate.setOnClickListener(this);
        add.setOnClickListener(this);
        clear.setOnClickListener(this);
        config.setOnClickListener(this);
        upload.setOnClickListener(this);
        start.setOnClickListener(this);
        stop.setOnClickListener(this);*/

    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // When the compile and target version is higher than 22, please request the
        // following permissions at runtime to ensure the
        // SDK work well.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE, Manifest.permission.VIBRATE,
                            Manifest.permission.INTERNET, Manifest.permission.ACCESS_WIFI_STATE,
                            Manifest.permission.WAKE_LOCK, Manifest.permission.ACCESS_COARSE_LOCATION,
                            Manifest.permission.ACCESS_NETWORK_STATE, Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.CHANGE_WIFI_STATE, Manifest.permission.MOUNT_UNMOUNT_FILESYSTEMS,
                            Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.SYSTEM_ALERT_WINDOW,
                            Manifest.permission.READ_PHONE_STATE,
                    }
                    , 1);
        }

        setContentView(R.layout.activity_main);

        IntentFilter filter = new IntentFilter();
        filter.addAction(DJIApplication.FLAG_CONNECTION_CHANGE);
        registerReceiver(mReceiver, filter);

        initUI();

        SupportMapFragment mapFragment = (SupportMapFragment) getSupportFragmentManager()
                .findFragmentById(R.id.map);
        mapFragment.getMapAsync(this);

        addListener();

        mAuthTask = new MissionTask(SharedPreference.getString("Username", MainActivity.this));
        mAuthTask.execute("");
        SystemClock.sleep(1000);
        try {
            if(SharedPreference.getString("NameMission", MainActivity.this) != null){

                if(!SharedPreference.getString("NameMission", MainActivity.this).equals("FAILED")) {
                    showAlertMessage("Connected", "The connection with the socket is successfully.");

                    mSocket = IO.socket(getResources().getString(url_host) + ":" + getResources().getString(port_socket) + "/start");
                    mSocket.on(Socket.EVENT_CONNECT, onConnect);
                    mSocket.on(Socket.EVENT_DISCONNECT, onDisconnect);
                    mSocket.on("message", onNewMessage);
                    //mSocket.on("user left", onUserLeft);
                    mSocket.connect();
                }
            }
            else{
                showAlertMessage(getResources().getString(no_mission_active_tittle),
                        getResources().getString(no_mission_active));
            }

        } catch (URISyntaxException e) {
            showAlertMessage("Error on socket", "We having some troubles with the " +
                    "connection to the socket.");
            e.printStackTrace();
        }

    }

    private void followMission(){
        getWaypointMissionOperator().uploadMission(new CommonCallbacks.CompletionCallback() {
            @Override
            public void onResult(DJIError error) {
                if (error == null) {
                    setResultToToast("Mission upload successfully!");
                    //emitMessageSocket("Mission upload successfully!");
                    SystemClock.sleep(500);
                    startWaypointMission();
                } else {
                    setResultToToast("Mission upload failed, error: " + error.getDescription() + " retrying...");
                    emitMessageSocket("Mission upload failed, error: " + error.getDescription() + " retrying...");
                    getWaypointMissionOperator().retryUploadMission(null);
                }
            }
        });
    }

    private void executeCommand(final String msg){
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try{
                    String[] commands = msg.split(" : ");

                    switch (commands[0]){
                        case "status":
                            incomingMsg.setText("Checking status from server");
                            emitMessageSocket("is online");
                            break;

                        case "land":
                            incomingMsg.setText("Landing the AirCraft");
                            landAirCraft();
                            break;

                        case "motors":
                            incomingMsg.setText("Stopping the motors");
                            stopMotors();
                            break;

                        case "destroy":
                            incomingMsg.setText("Destroy mission");
                            destroyWaypointMission();
                            break;

                        case "enable":
                            incomingMsg.setText("Enable add Waypoint");
                            enableDisableAdd();
                            break;

                        case "start":
                            incomingMsg.setText("Start mission");
                            //start mission
                            startWaypointMission();
                            break;

                        case "stop":
                            incomingMsg.setText("Stop mission");
                            //stop mission
                            stopWaypointMission();
                            break;

                        case "add":
                            incomingMsg.setText("Add Waypoint");
                            //add waypoint
                            double lat = Double.valueOf(commands[1]);
                            double lon = Double.valueOf(commands[2]);
                            LatLng point = new LatLng(lat, lon);
                            markWaypoint(point);
                            Waypoint mWaypoint = new Waypoint(point.latitude, point.longitude, altitude);
                            //Add Waypoints to Waypoint arraylist;
                            if (waypointMissionBuilder != null) {
                                waypointList.add(mWaypoint);
                                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
                            }else
                            {
                                waypointMissionBuilder = new WaypointMission.Builder();
                                waypointList.add(mWaypoint);
                                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
                            }
                            break;

                        case "upload":
                            incomingMsg.setText("Upload mission");
                            //upload mission
                            uploadWayPointMission();
                            break;

                        case "locate":
                            incomingMsg.setText("Locate device");
                            updateDroneLocation();
                            cameraUpdate(); // Locate the drone's place
                            String position = Double.toString(droneLocationLat) + " : " + Double.toString(droneLocationLng);
                            emitMessageSocket(position);
                            //JSONObject msgJson = new JSONObject();
                            //String newMsg = SharedPreference.getString("Username", MainActivity.this) + " # " + position;
                            //msgJson.put("msg", newMsg);
                            //mSocket.emit("textMobile", msgJson, SharedPreference.getString("NameMission", MainActivity.this));
                            //mSocket.emit("message", position, SharedPreference.getString("NameMission", MainActivity.this));
                            //locate uav
                            break;

                        case "clear":
                            incomingMsg.setText("Clear Waypoint");
                            //clear waypoints
                            if(waypointList.size() > 0){
                                gMap.clear();
                                waypointList.clear();
                                waypointMissionBuilder.waypointList(waypointList);
                                updateDroneLocation();
                            }
                            break;

                        case "follow":
                            incomingMsg.setText("Follow device");
                            //follow other UAV
                            waitingResponse = true;
                            emitMessageSocket(commands[1]+" # locateByUser");
                            break;

                        case "locateByUser":
                            incomingMsg.setText("Locating device by user");
                            String positions = Double.toString(droneLocationLat) + " : " + Double.toString(droneLocationLng);
                            getAltitude();
                            emitMessageSocket("responseByUser # response : "+ positions + " : " + altitude);
                            break;

                        case "response":
                            incomingMsg.setText("Response by user");
                            waitingResponse = false;
                            //Clear other waypoints
                            if(waypointList.size() > 0) {
                                gMap.clear();
                                waypointList.clear();
                                waypointMissionBuilder.waypointList(waypointList);
                                updateDroneLocation();
                            }

                            //Make my Waypoint
                            LatLng mePoint = new LatLng(droneLocationLat, droneLocationLng);
                            markWaypoint(mePoint);
                            Waypoint meWaypoint = new Waypoint(mePoint.latitude, mePoint.longitude, altitude);

                            //commands[1] lat
                            //commands[2] long
                            //commands[3] altitude
                            double otherLat = Double.valueOf(commands[1]);
                            double otherLon = Double.valueOf(commands[2]);
                            float otherAlt = Float.valueOf(commands[3]);
                            LatLng otherPoint = new LatLng(otherLat, otherLon);
                            markWaypoint(otherPoint);
                            Waypoint otherWaypoint = new Waypoint(otherPoint.latitude, otherPoint.longitude, otherAlt);

                            //Add Waypoints to Waypoint arraylist;
                            if (waypointMissionBuilder != null) {
                                waypointList.add(meWaypoint);
                                waypointList.add(otherWaypoint);
                                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
                            }else
                            {
                                waypointMissionBuilder = new WaypointMission.Builder();
                                waypointList.add(meWaypoint);
                                waypointList.add(otherWaypoint);
                                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
                            }

                            //Config the waypoints
                            mSpeed = 3.0f;
                            mFinishedAction = WaypointMissionFinishedAction.NO_ACTION;
                            mHeadingMode = WaypointMissionHeadingMode.AUTO;
                            altitude = otherAlt;
                            configWayPointMission();
                            SystemClock.sleep(500);
                            //upload and start mission
                            followMission();
                            break;

                        case "home":
                            //set home location
                            break;

                        case "config":
                            incomingMsg.setText("Config mission");
                            //config the mission
                            switch (commands[1]){ //for speed
                                case "low":
                                    //slow speed
                                    mSpeed = 3.0f;
                                    break;
                                case "mid":
                                    //mid speed
                                    mSpeed = 5.0f;
                                    break;
                                case "high":
                                    //high speed
                                    mSpeed = 10.0f;
                                    break;
                                default :
                                    break;
                            }
                            switch (commands[2]){ //for action before complete mission
                                case "no":
                                    //no action
                                    mFinishedAction = WaypointMissionFinishedAction.NO_ACTION;
                                    break;
                                case "home":
                                    //back to home
                                    mFinishedAction = WaypointMissionFinishedAction.GO_HOME;
                                    break;
                                case "land":
                                    //auto land
                                    mFinishedAction = WaypointMissionFinishedAction.AUTO_LAND;
                                    break;
                                case "first":
                                    //go to the first waypoint
                                    mFinishedAction = WaypointMissionFinishedAction.GO_FIRST_WAYPOINT;
                                    break;
                                default :
                                    break;
                            }

                            switch (commands[3]){ //for heading
                                case "auto":
                                    mHeadingMode = WaypointMissionHeadingMode.AUTO;
                                    break;
                                case "initial":
                                    mHeadingMode = WaypointMissionHeadingMode.USING_INITIAL_DIRECTION;
                                    break;
                                case "remote":
                                    mHeadingMode = WaypointMissionHeadingMode.CONTROL_BY_REMOTE_CONTROLLER;
                                    break;
                                case "waypoint":
                                    mHeadingMode = WaypointMissionHeadingMode.USING_WAYPOINT_HEADING;
                                    break;
                                default :
                                    break;
                            }
                            altitude = Integer.parseInt(nulltoIntegerDefalt(commands[4]));
                            configWayPointMission();
                            break;

                        default:
                            incomingMsg.setText("Error on Command");
                            break;
                    }

                } catch (NullPointerException ex) {
                    showAlertMessage("Error", "Error at parser message.");

                }
            }
        });

    }

    private Emitter.Listener onConnect = new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            if (!isConnected){
                mSocket.emit("join", SharedPreference.getString("NameMission", MainActivity.this), SharedPreference.getString("Username", MainActivity.this));
            }
        }
    };

    private Emitter.Listener onDisconnect = new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            mSocket.emit("left", MainActivity.this);
            mSocket.disconnect();
            Log.i(TAG, "diconnected");
            isConnected = false;
        }
    };

    private boolean isForMe(String userName){
        if (SharedPreference.getString("Username", MainActivity.this).equals(userName)){
            return true;
        }
        if (userName.equals("all")){
            return true;
        }
        if (userName.equals("responseByUser") && waitingResponse){
            return true;
        }
        else{
            return false;
        }
    }

    private Emitter.Listener onNewMessage = new Emitter.Listener() {
        @Override
        public void call(final Object... args) {
            JSONObject data = (JSONObject) args[0];
            try {
                String command = data.getString("msg");
                String[] splitedString = command.split(" # ");
                //splitedString[0] -> admin
                //splitedString[1] -> user/all/responsebyuser
                //splitedString[2] -> commands
                //showAlertMessage("mensaje", "1: "+splitedString[0]+" 2: "+splitedString[1]+" 3: "+splitedString[2]);
                //showMe(splitedString);
                if (isForMe(splitedString[1].replace(" ", ""))){
                    executeCommand(splitedString[2]);
                }

            } catch (JSONException e) {
                Log.e(TAG, e.getMessage());
                return;
            }

        }
    };

    private void emitMessageSocket(String message){
        String endpoints = "textMobile";
        String newMsg = SharedPreference.getString("Username", MainActivity.this) + " # " + message;
        JSONObject msgJson = new JSONObject();
        try {
            msgJson.put("msg", newMsg);
        } catch (JSONException e) {
            e.printStackTrace();
        }
        mSocket.emit(endpoints, msgJson, SharedPreference.getString("NameMission", MainActivity.this));
    }

    protected BroadcastReceiver mReceiver = new BroadcastReceiver() {

        @Override
        public void onReceive(Context context, Intent intent) {
            onProductConnectionChange();
        }
    };

    private void onProductConnectionChange()
    {
        initFlightController();
        loginAccount();
    }

    private void loginAccount(){

        UserAccountManager.getInstance().logIntoDJIUserAccount(this,
                new CommonCallbacks.CompletionCallbackWith<UserAccountState>() {
                    @Override
                    public void onSuccess(final UserAccountState userAccountState) {
                        Log.e(TAG, "Login Success");
                    }
                    @Override
                    public void onFailure(DJIError error) {
                        setResultToToast("Login Error:"
                                + error.getDescription());
                    }
                });
    }

    private void showAlertMessage(String title, String message){
        AlertDialog alertDialog = new AlertDialog.Builder(MainActivity.this).create();
        alertDialog.setTitle(title);
        alertDialog.setMessage(message);
        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int which) {
                        dialog.dismiss();
                    }
                });
        alertDialog.show();
    }

    private void initFlightController() {

        BaseProduct product = DJIApplication.getProductInstance();
        if (product != null && product.isConnected()) {
            if (product instanceof Aircraft) {
                mFlightController = ((Aircraft) product).getFlightController();
            }
        }

        if (mFlightController != null) {
            mFlightController.setStateCallback(new FlightControllerState.Callback() {

                @Override
                public void onUpdate(FlightControllerState djiFlightControllerCurrentState) {
                    droneLocationLat = djiFlightControllerCurrentState.getAircraftLocation().getLatitude();
                    droneLocationLng = djiFlightControllerCurrentState.getAircraftLocation().getLongitude();
                    updateDroneLocation();
                }
            });
        }
    }

    //Add Listener for WaypointMissionOperator
    private void addListener() {
        if (getWaypointMissionOperator() != null){
            getWaypointMissionOperator().addListener(eventNotificationListener);
        }
    }

    private void removeListener() {
        if (getWaypointMissionOperator() != null) {
            getWaypointMissionOperator().removeListener(eventNotificationListener);
        }
    }

    private WaypointMissionOperatorListener eventNotificationListener = new WaypointMissionOperatorListener() {
        @Override
        public void onDownloadUpdate(WaypointMissionDownloadEvent downloadEvent) {

        }

        @Override
        public void onUploadUpdate(WaypointMissionUploadEvent uploadEvent) {

        }

        @Override
        public void onExecutionUpdate(WaypointMissionExecutionEvent executionEvent) {

        }

        @Override
        public void onExecutionStart() {

        }

        @Override
        public void onExecutionFinish(@Nullable final DJIError error) {
            setResultToToast("Execution finished: " + (error == null ? "Success!" : error.getDescription()));
        }
    };

    public WaypointMissionOperator getWaypointMissionOperator() {
        if (instance == null) {
            if (DJISDKManager.getInstance().getMissionControl() != null){
                instance = DJISDKManager.getInstance().getMissionControl().getWaypointMissionOperator();
            }
        }
        return instance;
    }

    private void setUpMap() {
        gMap.setOnMapClickListener(this);// add the listener for click for amap object

    }

    @Override
    public void onMapClick(LatLng point) {
        if (isAdd == true){
            markWaypoint(point);
            Waypoint mWaypoint = new Waypoint(point.latitude, point.longitude, altitude);
            //Add Waypoints to Waypoint arraylist;
            if (waypointMissionBuilder != null) {
                waypointList.add(mWaypoint);
                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
            }else
            {
                waypointMissionBuilder = new WaypointMission.Builder();
                waypointList.add(mWaypoint);
                waypointMissionBuilder.waypointList(waypointList).waypointCount(waypointList.size());
            }
        }else{
            setResultToToast("Cannot Add Waypoint");
        }
    }

    public static boolean checkGpsCoordination(double latitude, double longitude) {
        return (latitude > -90 && latitude < 90 && longitude > -180 && longitude < 180) && (latitude != 0f && longitude != 0f);
    }

    // Update the drone location based on states from MCU.
    private void updateDroneLocation(){

        LatLng pos = new LatLng(droneLocationLat, droneLocationLng);
        //Create MarkerOptions object
        final MarkerOptions markerOptions = new MarkerOptions();
        markerOptions.position(pos);
        markerOptions.icon(BitmapDescriptorFactory.fromResource(R.drawable.aircraft));

        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (droneMarker != null) {
                    droneMarker.remove();
                }

                if (checkGpsCoordination(droneLocationLat, droneLocationLng)) {
                    droneMarker = gMap.addMarker(markerOptions);
                }
            }
        });
    }

    private void markWaypoint(LatLng point){
        //Create MarkerOptions object
        MarkerOptions markerOptions = new MarkerOptions();
        markerOptions.position(point);
        markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_BLUE));
        Marker marker = gMap.addMarker(markerOptions);
        mMarkers.put(mMarkers.size(), marker);
    }

    private void cancelMission() {
        emitMessageSocket("El usuario "+
                SharedPreference.getString("Username", MainActivity.this)
                + " ha dejado la misión!");
        getWaypointMissionOperator().stopMission(new CommonCallbacks.CompletionCallback() {
            @Override
            public void onResult(DJIError error) {
                if (error == null){
                    landAirCraft();
                }

                setResultToToast("Mission Stop: " + (error == null ? "Successfully" : error.getDescription()));
                emitMessageSocket("Mission Stop: " + (error == null ? "Successfully" : error.getDescription()));
            }
        });
    }

    @Override
    public void onClick(View v) {
        switch (v.getId()) {
            case R.id.cancelMission:{
                cancelMission();
                showAlertMessage("Misión Cancelada", "La misión ha sido cancelada!");
                break;
            }

            default:
                break;

            /*case R.id.locate:{
                updateDroneLocation();
                cameraUpdate(); // Locate the drone's place
                break;
            }
            case R.id.add:{
                enableDisableAdd();
                break;
            }
            case R.id.clear:{
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        gMap.clear();
                    }

                });
                waypointList.clear();
                waypointMissionBuilder.waypointList(waypointList);
                updateDroneLocation();
                break;
            }
            case R.id.config:{
                showSettingDialog();
                break;
            }
            case R.id.upload:{
                uploadWayPointMission();
                break;
            }
            case R.id.start:{
                startWaypointMission();
                break;
            }
            case R.id.stop:{
                stopWaypointMission();
                break;
            }
            default:
                break;*/
        }
    }

    private void cameraUpdate(){
        LatLng pos = new LatLng(droneLocationLat, droneLocationLng);
        float zoomlevel = (float) 18.0;
        CameraUpdate cu = CameraUpdateFactory.newLatLngZoom(pos, zoomlevel);
        gMap.moveCamera(cu);

    }

    private void enableDisableAdd(){
        if (isAdd == false) {
            isAdd = true;
            //add.setText("Exit");
        }else{
            isAdd = false;
            //add.setText("Add");
        }
    }

    private void showSettingDialog(){
        LinearLayout wayPointSettings = (LinearLayout)getLayoutInflater().inflate(R.layout.dialog_waypointsetting, null);

        final TextView wpAltitude_TV = (TextView) wayPointSettings.findViewById(R.id.altitude);
        RadioGroup speed_RG = (RadioGroup) wayPointSettings.findViewById(R.id.speed);
        RadioGroup actionAfterFinished_RG = (RadioGroup) wayPointSettings.findViewById(R.id.actionAfterFinished);
        RadioGroup heading_RG = (RadioGroup) wayPointSettings.findViewById(R.id.heading);

        speed_RG.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener(){

            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                if (checkedId == R.id.lowSpeed){
                    mSpeed = 3.0f;
                } else if (checkedId == R.id.MidSpeed){
                    mSpeed = 5.0f;
                } else if (checkedId == R.id.HighSpeed){
                    mSpeed = 10.0f;
                }
            }

        });

        actionAfterFinished_RG.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener() {

            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                Log.d(TAG, "Select finish action");
                if (checkedId == R.id.finishNone){
                    mFinishedAction = WaypointMissionFinishedAction.NO_ACTION;
                } else if (checkedId == R.id.finishGoHome){
                    mFinishedAction = WaypointMissionFinishedAction.GO_HOME;
                } else if (checkedId == R.id.finishAutoLanding){
                    mFinishedAction = WaypointMissionFinishedAction.AUTO_LAND;
                } else if (checkedId == R.id.finishToFirst){
                    mFinishedAction = WaypointMissionFinishedAction.GO_FIRST_WAYPOINT;
                }
            }
        });

        heading_RG.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener() {

            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                Log.d(TAG, "Select heading");

                if (checkedId == R.id.headingNext) {
                    mHeadingMode = WaypointMissionHeadingMode.AUTO;
                } else if (checkedId == R.id.headingInitDirec) {
                    mHeadingMode = WaypointMissionHeadingMode.USING_INITIAL_DIRECTION;
                } else if (checkedId == R.id.headingRC) {
                    mHeadingMode = WaypointMissionHeadingMode.CONTROL_BY_REMOTE_CONTROLLER;
                } else if (checkedId == R.id.headingWP) {
                    mHeadingMode = WaypointMissionHeadingMode.USING_WAYPOINT_HEADING;
                }
            }
        });

        new AlertDialog.Builder(this)
                .setTitle("")
                .setView(wayPointSettings)
                .setPositiveButton("Finish",new DialogInterface.OnClickListener(){
                    public void onClick(DialogInterface dialog, int id) {

                        String altitudeString = wpAltitude_TV.getText().toString();
                        altitude = Integer.parseInt(nulltoIntegerDefalt(altitudeString));
                        Log.e(TAG,"altitude "+altitude);
                        Log.e(TAG,"speed "+mSpeed);
                        Log.e(TAG, "mFinishedAction "+mFinishedAction);
                        Log.e(TAG, "mHeadingMode "+mHeadingMode);
                        configWayPointMission();
                    }

                })
                .setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int id) {
                        dialog.cancel();
                    }

                })
                .create()
                .show();
    }

    String nulltoIntegerDefalt(String value){
        if(!isIntValue(value)) value="0";
        return value;
    }

    boolean isIntValue(String val)
    {
        try {
            val=val.replace(" ","");
            Integer.parseInt(val);
        } catch (Exception e) {return false;}
        return true;
    }

    private void configWayPointMission(){

        if (waypointMissionBuilder == null){

            waypointMissionBuilder = new WaypointMission.Builder().finishedAction(mFinishedAction)
                    .headingMode(mHeadingMode)
                    .autoFlightSpeed(mSpeed)
                    .maxFlightSpeed(mSpeed)
                    .flightPathMode(WaypointMissionFlightPathMode.NORMAL);

        }else
        {
            waypointMissionBuilder.finishedAction(mFinishedAction)
                    .headingMode(mHeadingMode)
                    .autoFlightSpeed(mSpeed)
                    .maxFlightSpeed(mSpeed)
                    .flightPathMode(WaypointMissionFlightPathMode.NORMAL);

        }

        if (waypointMissionBuilder.getWaypointList().size() > 0){

            for (int i=0; i< waypointMissionBuilder.getWaypointList().size(); i++){
                waypointMissionBuilder.getWaypointList().get(i).altitude = altitude;
            }

            setResultToToast("Set Waypoint attitude successfully");
            emitMessageSocket("Set Waypoint attitude successfully");
        }

        DJIError error = getWaypointMissionOperator().loadMission(waypointMissionBuilder.build());
        if (error == null) {
            setResultToToast("loadWaypoint succeeded");
            emitMessageSocket("loadWaypoint succeeded");
        } else {
            setResultToToast("loadWaypoint failed " + error.getDescription());
            emitMessageSocket("loadWaypoint failed " + error.getDescription());
        }
    }

    private void uploadWayPointMission(){

        getWaypointMissionOperator().uploadMission(new CommonCallbacks.CompletionCallback() {
            @Override
            public void onResult(DJIError error) {
                if (error == null) {
                    setResultToToast("Mission upload successfully!");
                    emitMessageSocket("Mission upload successfully!");
                } else {
                    setResultToToast("Mission upload failed, error: " + error.getDescription() + " retrying...");
                    emitMessageSocket("Mission upload failed, error: " + error.getDescription() + " retrying...");
                    getWaypointMissionOperator().retryUploadMission(null);
                }
            }
        });

    }

    private void startWaypointMission(){
        getWaypointMissionOperator().startMission(new CommonCallbacks.CompletionCallback() {
            @Override
            public void onResult(DJIError error) {
                setResultToToast("Mission Start: " + (error == null ? "Successfully" : error.getDescription()));
                emitMessageSocket("Mission Start: " + (error == null ? "Successfully" : error.getDescription()));
            }
        });
    }

    private void stopWaypointMission(){
        getWaypointMissionOperator().stopMission(new CommonCallbacks.CompletionCallback() {
            @Override
            public void onResult(DJIError error) {
                setResultToToast("Mission Stop: " + (error == null ? "Successfully" : error.getDescription()));
                emitMessageSocket("Mission Stop: " + (error == null ? "Successfully" : error.getDescription()));
            }
        });

    }

    private void destroyWaypointMission(){
        getWaypointMissionOperator().destroy();
    }

    private void landAirCraft() {
        if(mFlightController != null) {
            mFlightController.startLanding(new CommonCallbacks.CompletionCallback() {
               @Override
               public void onResult(DJIError error) {
                   setResultToToast("Start landing: " + (error == null ? "Successfully" : error.getDescription()));
                   emitMessageSocket("Start landing: " + (error == null ? "Successfully" : error.getDescription()));
               }
            });
        } else {
            setResultToToast("Start landing: FlightController is null.");
        }
    }

    private void getAltitude(){
        if(mFlightController != null){
            mFlightController.setStateCallback(new FlightControllerState.Callback() {

                @Override
                public void onUpdate(FlightControllerState state) {
                    final float maltitude = state.getAircraftLocation().getAltitude();
                    //Do something with altitude value
                    altitude = maltitude;
                }
            });
        }
    }

    private void stopMotors(){
        if(mFlightController != null){
            mFlightController.turnOffMotors(new CommonCallbacks.CompletionCallback() {
                @Override
                public void onResult(DJIError error) {
                    setResultToToast("Stop motors: " + (error == null ? "Successfully" : error.getDescription()));
                    emitMessageSocket("Stop motors: " + (error == null ? "Successfully" : error.getDescription()));
                }
            });
        } else {
            setResultToToast("Start landing: FlightController is null.");
            emitMessageSocket("Start landing: FlightController is null");
        }
    }

    @Override
    public void onMapReady(GoogleMap googleMap) {
        if (gMap == null) {
            gMap = googleMap;
            setUpMap();
        }

        LatLng shenzhen = new LatLng(22.5362, 113.9454);
        gMap.addMarker(new MarkerOptions().position(shenzhen).title("Marker in Shenzhen"));
        gMap.moveCamera(CameraUpdateFactory.newLatLng(shenzhen));
    }

    public class MissionTask extends AsyncTask<String, Void, String> {

        private final String mUsername;

        MissionTask(String usernname) {
            mUsername = usernname;
        }

        @Override
        protected String doInBackground(String... params) {
            OkHttpClient client = new OkHttpClient();
            HttpUrl.Builder urlBuilder = HttpUrl.parse(getResources().getString(url_host)+":"+getResources().getString(port_api)+"/getmission/"+mUsername).newBuilder();


            String url = urlBuilder.build().toString();
            Request request = new Request.Builder()
                    .url(url)
                    .build();

            try (Response response = client.newCall(request).execute()) {
                if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
                return response.body().string();

            } catch (IOException e) {
                e.printStackTrace();
            }
            return "FAILED";
        }

        @Override
        protected void onPostExecute(String result) {
            mAuthTask = null;
            if (!result.equals("FAILED")) {
                SharedPreference.setString("NameMission", result, MainActivity.this);
            } else {
                SharedPreference.setString("NameMission", "FAILED", MainActivity.this);
            }
        }

        @Override
        protected void onPreExecute() {}

        @Override
        protected void onProgressUpdate(Void... values) {}
    }
}
