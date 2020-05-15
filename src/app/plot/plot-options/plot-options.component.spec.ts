import { Select2Module } from 'ng2-select2';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { PlotOptionsComponent } from './plot-options.component';
import { HttpClientModule } from '@angular/common/http';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { DimensionOptionsComponent } from './dimension-options/dimension-options.component';
import { PlotBuilder, Dimension } from 'src/app/shared/models/plot-builder';
import { ObjectMetadata } from 'src/app/shared/models/object-metadata';
import { PlotService } from 'src/app/shared/services/plot.service';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { of } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { Select2OptionData } from 'ng2-select2';

describe('PlotOptionsComponent', () => {

  const MockPlotService = {
    getPlotBuilder: () => new PlotBuilder(),
    getPlotTypes: () => of({
      results: [
        {
          axis_blocks: [
            {title: 'X axis'},
            {titls: 'Y axis'}
          ],
          description: '1D Vertical Barchart',
          image_tag: '<i class="material-icons"></i>',
          n_dimensions: 2,
          name: 'Vertical Barchart',
          plotly_layout: {},
          plotly_trace: {
            type: 'bar'
          }
        }
      ]
    }),
    getPlotType: () => null,
    setConfig: (name, length, callback) => {
      callback([new Dimension(), new Dimension()]);
    }
  };

  const metadata = new ObjectMetadata();
  metadata.data_type = {
    oterm_name: 'Microbial Sequence',
    oterm_ref: 'DA:0000064'
  };
  metadata.typed_values = [
    {
      value_type: {
        oterm_ref: 'ME:0000002',
        oterm_name: 'Test DataVar'
      }
    }
  ];
  metadata.dim_context = [
    {
      data_type: {
        oterm_ref: 'DA0000064',
        oterm_name: 'Microbial Sequence'
      },
      size: 1083,
      typed_values: [{
        value_context: [],
        value_no_units: 'Strain ID',
        value_type: {
          oterm_ref: 'ME:0000044',
          oterm_name: 'Srain ID'
        },
        value_with_units: 'Strain ID',
        values: {
          scalar_type: 'object_ref',
          values: ['FW305-130', '...']
        }
      }]
    },
    {
      data_type: {
        oterm_ref: 'DA0000064',
        oterm_name: 'Microbial Sequence'
      },
      size: 1083,
      typed_values: [{
        value_context: [],
        value_no_units: 'Strain ID',
        value_type: {
          oterm_ref: 'ME:0000044',
          oterm_name: 'Srain ID'
        },
        value_with_units: 'Strain ID',
        values: {
          scalar_type: 'object_ref',
          values: ['FW305-130', '...']
        }
      }]
    }
  ];

  const MockQueryBuilder = {
    getPreviousUrl: () => 'plot/test/url',
    getObjectMetadata: (id) => of(metadata)
  };

  let spectator: Spectator<PlotOptionsComponent>;
  const createComponent = createComponentFactory({
    component: PlotOptionsComponent,
    entryComponents: [
      MockComponent(DimensionOptionsComponent)
    ],
    imports: [
      FormsModule,
      RouterModule.forRoot([]),
      Select2Module,
      HttpClientModule
    ],
    providers: [
      mockProvider(PlotService, MockPlotService),
      mockProvider(QueryBuilderService, MockQueryBuilder),
      {
        provide: ActivatedRoute,
        useValue: {
          params: of({id: 'Brick0000002'})
        }
      },
      {
        provide: Router,
        useValue: {
          events: of({
            url: '/plot/options/Brick0000002'
          })
        }
      }
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should get object id from url', () => {
    expect(spectator.component.objectId).toBe('Brick0000002');
  });

  it('should have previous url', () => {
    spyOn(MockQueryBuilder, 'getPreviousUrl').and.callThrough();
    expect(spectator.component.previousUrl).toBe('plot/test/url');
  });

  it('should get plot types correctly', () => {
    const comp = spectator.component;
    spyOn(comp, 'getPlotTypes').and.callThrough();
    spectator.detectChanges();
    expect(comp.listPlotTypes instanceof Array).toBeTruthy();
    expect(comp.listPlotTypes).toHaveLength(1);

    // should be greater than 1 including default empty select2 value
    expect(comp.plotTypeData.length).toBeGreaterThan(1);
    expect(comp.plotTypeData[1]).toEqual({id: '0', text: 'Vertical Barchart'});
  });

  it('should add correct number of dimensions', () => {
    spectator.component.updatePlotType({
      value: '0', data: [{
        text: '1D Vertical Barchart',
        id: '0'
      }]
    });
    spectator.detectChanges();
    expect(spectator.component.axisBlocks).not.toBeUndefined();
    expect(spectator.component.selectedPlotType).not.toBeUndefined();
    expect(spectator.queryAll('app-dimension-options')).toHaveLength(2);
  });
});
