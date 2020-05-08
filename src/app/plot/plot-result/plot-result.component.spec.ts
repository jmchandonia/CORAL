import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { PlotResultComponent } from './plot-result.component';
import { PlotlyModule } from 'angular-plotly.js';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';

describe('PlotResultComponent', () => {
  // let component: PlotResultComponent;
  // let fixture: ComponentFixture<PlotResultComponent>;
  PlotlyModule.plotlyjs = PlotlyJS;
  let spectator: Spectator<PlotResultComponent>;
  const createComponent = createComponentFactory({
    component: PlotResultComponent,
    imports: [
      PlotlyModule,
      NgxSpinnerModule,
      HttpClientModule,
      RouterModule.forRoot([])
    ]
  });

  // beforeEach(async(() => {
  //   // TestBed.configureTestingModule({
  //   //   declarations: [ PlotResultComponent ]
  //   // })
  //   // .compileComponents();
  //   spectator = createComponent();
  // }));

  // beforeEach(() => {
  //     fixture = TestBed.createComponent(PlotResultComponent);
  //     component = fixture.componentInstance;
  //     fixture.detectChanges();
  // });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    // expect(component).toBeTruthy();
    expect(spectator.component).toBeTruthy();
  });
});
