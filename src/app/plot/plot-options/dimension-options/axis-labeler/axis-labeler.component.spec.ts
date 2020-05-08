import { async, ComponentFixture, TestBed } from '@angular/core/testing';
// import { AppModule } from 'src/app/app.module';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { PlotService } from  'src/app/shared/services/plot.service';
import { AxisLabelerComponent } from './axis-labeler.component';
import { DimensionRef, Dimension } from 'src/app/shared/models/plot-builder';
import { Subject } from 'rxjs';


describe('AxisLabelerComponent', () => {

  const MockPlotService = {
    getLabelBuilder: () => new DimensionRef('test', []),
    getUpdatedLabelBuilder: () => new Subject()
  };

  let spectator: Spectator<AxisLabelerComponent>;
  const createComponent = createComponentFactory({
    component: AxisLabelerComponent,
    imports: [
      FormsModule,
      HttpClientModule
    ],
    providers: [
      mockProvider(PlotService, MockPlotService)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimension: new Dimension()
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
