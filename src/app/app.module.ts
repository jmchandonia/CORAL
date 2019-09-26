import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { SearchModule } from './search/search.module';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { PlotModule } from './plot/plot.module';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { PlotlyModule } from 'angular-plotly.js';
import { LoginComponent } from './shared/components/login/login.component';
import { HomeComponent } from './shared/components/home/home.component';
import { ReportsComponent } from './shared/components/reports/reports.component';
import { UploadComponent } from './shared/components/upload/upload.component';
import { DashboardComponent } from './shared/components/dashboard/dashboard.component';
import { NgxSpinnerModule } from 'ngx-spinner';

PlotlyModule.plotlyjs = PlotlyJS;
@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    HomeComponent,
    ReportsComponent,
    UploadComponent,
    DashboardComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SearchModule,
    HttpClientModule,
    Select2Module,
    PlotModule,
    NgxSpinnerModule,
    PlotlyModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
