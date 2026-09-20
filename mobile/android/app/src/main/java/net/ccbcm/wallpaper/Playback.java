package net.ccbcm.wallpaper;
import android.content.Context;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.view.SurfaceHolder;
import androidx.media3.common.*;
import androidx.media3.exoplayer.*;
import androidx.media3.exoplayer.mediacodec.MediaCodecSelector;
import java.io.File;
import java.util.ArrayList;

@androidx.annotation.OptIn(markerClass=androidx.media3.common.util.UnstableApi.class)
final class Playback {
 interface Events { void ready(boolean compatibility); void status(String message); void failed(String code); }
 final Context context; final File file; final SurfaceHolder surface; final Events events;
 final Handler handler=new Handler(Looper.getMainLooper());
 ExoPlayer player; boolean closed, firstFrame, playing, compatibility; int generation; Runnable timeout;
 Playback(Context c,File f,SurfaceHolder s,boolean mode,Events e){context=c;file=f;surface=s;compatibility=mode;events=e;}
 void start(){
  if(closed||!surface.getSurface().isValid())return;
  dispose();firstFrame=false;final int run=++generation;
  try{
   DefaultRenderersFactory renderers=new DefaultRenderersFactory(context).setEnableDecoderFallback(true);
   if(compatibility){
    renderers.forceDisableMediaCodecAsynchronousQueueing();
    renderers.setMediaCodecSelector((mime,secure,tunneling)->{
     ArrayList<androidx.media3.exoplayer.mediacodec.MediaCodecInfo> list=new ArrayList<>(MediaCodecSelector.DEFAULT.getDecoderInfos(mime,secure,tunneling));
     list.sort((a,b)->Boolean.compare(b.softwareOnly,a.softwareOnly));return list;
    });
   }
   player=new ExoPlayer.Builder(context,renderers).build();
   player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_AUDIO,true).build());
   player.setVolume(0);player.setRepeatMode(Player.REPEAT_MODE_ONE);
   player.setVideoScalingMode(C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING);
   player.addListener(new Player.Listener(){
    @Override public void onRenderedFirstFrame(){if(closed||run!=generation)return;firstFrame=true;cancelTimeout();events.ready(compatibility);}
    @Override public void onPlayerError(PlaybackException error){if(closed||run!=generation)return;recover(error.getErrorCodeName(),run);}
   });
   player.setVideoSurfaceHolder(surface);player.setMediaItem(MediaItem.fromUri(Uri.fromFile(file)));player.prepare();player.setPlayWhenReady(playing);armTimeout(run);
  }catch(Exception error){recover(error.getClass().getSimpleName(),run);}
 }
 void recover(String code,int run){
  // Recreate outside listener dispatch; never hold two decoders for a retry.
  handler.post(()->{if(closed||run!=generation)return;dispose();
   if(!compatibility){compatibility=true;events.status("正在尝试兼容播放…");start();}
   else{generation++;events.failed(code);}
  });
 }
 void armTimeout(int run){cancelTimeout();if(!playing||firstFrame)return;timeout=()->recover("FIRST_FRAME_TIMEOUT",run);handler.postDelayed(timeout,12000);}
 void cancelTimeout(){if(timeout!=null){handler.removeCallbacks(timeout);timeout=null;}}
 void setPlaying(boolean value){playing=value;if(player!=null)player.setPlayWhenReady(value);if(value&&player!=null)armTimeout(generation);else cancelTimeout();}
 void dispose(){cancelTimeout();if(player!=null){player.release();player=null;}}
 void close(){closed=true;generation++;dispose();handler.removeCallbacksAndMessages(null);}
}
