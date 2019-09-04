import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { SearchModule } from './search/search.module';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component'; 
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { PlotModule } from './plot/plot.module';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SearchModule,
    HttpClientModule,
    Select2Module,
    PlotModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
