import { FormsModule } from '@angular/forms';
import { fakeAsync, tick } from '@angular/core/testing';
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
import { SafeHtmlPipe } from 'src/app/shared/pipes/safe-html.pipe';
import { NgSelectModule } from  '@ng-select/ng-select';
import { ActivatedRoute, Router } from '@angular/router';
import { PlotlyBuilder } from 'src/app/shared/models/plotly-builder';
import { PlotValidatorService as Validator } from 'src/app/shared/services/plot-validator.service';
const plotTypes = require('src/app/shared/test/plot-types.json');
// const metadata = require('src/app/shared/test/object-metadata.json');
const brick3Metadata = require('src/app/shared/test/brick_metadata_test_3.json');

describe('PlotOptionsComponent', () => {

  let coreTypeQueryParams = {}
  let brickId = 'Brick0000003'

  const MockPlotService = {
    getPlotlyBuilder: (core_type = false, query?) => new PlotlyBuilder(core_type, query),
    getObjectPlotMetadata: id => of({
      result: brick3Metadata,
      axisOptions: PlotService.mapBrickPropertiesToAxisOptions(brick3Metadata)
    }),
    getPlotTypes: () => of(plotTypes),
    getPlotType: () => null,
  };

  const MockQueryBuilder = {
    getPreviousUrl: () => 'plot/test/url',
    getObjectMetadata: (id) => of(brick3Metadata)
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
      NgSelectModule,
      HttpClientModule,
    ],
    declarations: [SafeHtmlPipe],
    providers: [
      mockProvider(PlotService, MockPlotService),
      mockProvider(QueryBuilderService, MockQueryBuilder),
      {
        provide: ActivatedRoute,
        useValue: {
          params: of({id: brickId}),
          queryParams: of(coreTypeQueryParams)
        }
      },
      {
        provide: Router,
        useValue: {
          events: of({
            url: '/plot/options/Brick0000003'
          }),
          navigate() {}
        }
      }
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should get object id from url', () => {
    expect(spectator.component.objectId).toBe('Brick0000003');
    expect(spectator.component.plot.core_type).toBeFalsy();
  });

  it('should call get plot metadata for bricks', () => {
    const mockPlotService = spectator.get(PlotService);
    spyOn(mockPlotService, 'getObjectPlotMetadata').and.callThrough();
    spectator.component.ngOnInit();
    spectator.detectChanges();
    expect(mockPlotService.getObjectPlotMetadata).toHaveBeenCalledWith('Brick0000003');
    expect(spectator.component.axisOptions).toHaveLength(7);
  });

  it('should filter plot types by validating', () => {
    // spyOn(spectator.component, 'validateAxes').and.callThrough();
    spyOn(Validator, 'getValidPlotTypes').and.callThrough();

    spectator.component.ngOnInit();
    // expect(spectator.component.validateAxes).toHaveBeenCalled();
    expect(Validator.getValidPlotTypes).toHaveBeenCalled();
    expect(spectator.component.plotTypeData).toHaveLength(5);
    expect(spectator.component.unableToPlot).toBeFalsy();
    expect(spectator.component.plotTypeData.find(plot => plot.map)).toBeUndefined();
  });

  it('should update plot type', () => {
    spyOn(spectator.component.plot, 'setDimensionConstraints').and.callThrough();

    spectator.triggerEventHandler('#plot-type-selector', 'change', spectator.component.plotTypeData[0]);
    expect(spectator.component.plot.setDimensionConstraints).toHaveBeenCalled();
    expect(spectator.component.plot.axes.z).toBeUndefined();
    expect(spectator.component.plot.constraints).toHaveLength(3);
    expect(spectator.component.plot.plot_type).toEqual(spectator.component.plotTypeData[0]);
  });

  it('should handle selecting an axis across all axis values', () => {
    spyOn(spectator.component, 'handleSelectedAxis').and.callThrough();
    // plot type must be selected first
     // manually set value for dimension (handled in axis option component)
    spectator.component.plot.axes.x.data = spectator.component.axisOptions[0];
    spectator.triggerEventHandler('#plot-type-selector', 'change', spectator.component.plotTypeData[0]);
    // select item from x axis dropdown
    spectator.triggerEventHandler('#x-axis', 'selected', spectator.component.axisOptions[0]);

    expect(spectator.component.handleSelectedAxis).toHaveBeenCalled();
    // with a 2d item, there should only be one axis option left because the last item has to be a data var
    expect(spectator.component.axisOptions).toHaveLength(1);
    expect(spectator.component.axisOptions[0].data_variable).toBe(0);
  });

  it('should handle clearing an axis correctly', () => {
    delete spectator.component.plot.axes.x.data;
    spectator.triggerEventHandler('#x-axis', 'selectionCleared', null);
    spectator.detectChanges();

    expect(spectator.component.axisOptions).toHaveLength(7);
  });

  it('should not navigate if plot is invalid', () => {
    const router = spectator.get(Router);
    spyOn(router, 'navigate');
    spectator.click('#submit-plot');
    spectator.detectChanges();

    expect (spectator.component.invalid).toBeTruthy();
    expect(router.navigate).not.toHaveBeenCalled();

    brickId = null;
    coreTypeQueryParams = { coreType: 'Well' }
  });
});
