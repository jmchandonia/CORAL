import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { PlotResultComponent } from './plot-result.component';
import { PlotlyModule } from 'angular-plotly.js';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { PlotService } from 'src/app/shared/services/plot.service';
import { of } from 'rxjs';
import { TooltipDirective, TooltipModule } from 'ngx-bootstrap/tooltip';

describe('PlotResultComponent', () => {
  PlotlyModule.plotlyjs = PlotlyJS;
  let spectator: Spectator<PlotResultComponent>;

  const MockPlotService = {
    getDynamicPlot: () => of({
      error: "",
      results: {
        data: [{
          type: "bar",
          x: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
          y: [1, 2, 3, 4, 5, 6, 7]
        }],
        layout: {
          height: 600,
          title: {
            text: 'Test Plot Result'
          },
          width: 800,
          xaxis: {
            automargin: true,
            type: "category",
            autorange: true,
            range: [0,8],
            title: {
              text: ''
            },
          yaxis: {
            automargin: true,
            autorange: true,
            range: [0,8],
            title: { text: '' },
            type: "linear"
          }
          }
        }
      },
      status: "OK"
    }),
    getCorePlot: () => of({
      error: "",
      results: {
        data: [{
          type: "bar",
          x: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
          y: [1, 2, 3, 4, 5, 6, 7]
        }],
        layout: {
          height: 600,
          title: {
            text: 'Test Plot Result'
          },
          width: 800,
          xaxis: {
            automargin: true,
            type: "category",
            autorange: true,
            range: [0,8],
            title: {
              text: ''
            },
          yaxis: {
            automargin: true,
            autorange: true,
            range: [0,8],
            title: { text: '' },
            type: "linear"
          }
          }
        }
      },
      status: "OK"
    })
  }

  const createComponent = createComponentFactory({
    component: PlotResultComponent,
    imports: [
      PlotlyModule,
      NgxSpinnerModule,
      HttpClientModule,
      RouterModule.forRoot([]),
      TooltipModule.forRoot()
    ],
    providers: [
      {
        provide: ActivatedRoute, 
        useValue: {
          params: of({id: 'brick0000002'}),
          queryParams: of({coreType: 'true'})
        },
      },
      mockProvider(PlotService, MockPlotService)
    ],
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have layout of 800 X 600', () => {
    const { width, height } = spectator.component.layout;
    expect(width).toBe(800);
    expect(height).toBe(600);
  });

  it('should get plot data', () => {
    expect(spectator.component.data).toEqual(
      [{
        type: "bar",
        x: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        y: [1, 2, 3, 4, 5, 6, 7]
      }]);
      expect(spectator.component.layout).toEqual({
        height: 600,
        title: {
          text: 'Test Plot Result'
        },
        width: 800,
        xaxis: {
          automargin: true,
          type: "category",
          autorange: true,
          range: [0,8],
          title: {
            text: ''
          },
          yaxis: {
            automargin: true,
            autorange: true,
            range: [0,8],
            title: { text: '' },
            type: "linear"
          }
        }
      });
  });

  it('should create shareable plot URL', () => {
    spyOn(spectator.component.plot, 'getPlotShareableUrl');
    spyOn(document, 'execCommand');

    spectator.click('button#share-plot');
    expect(spectator.component.plot.getPlotShareableUrl).toHaveBeenCalled();
    expect(document.execCommand).toHaveBeenCalledWith('copy');
  })
});
