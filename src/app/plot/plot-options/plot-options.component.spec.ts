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
import { SafeHtmlPipe } from 'src/app/shared/pipes/safe-html.pipe';
import { NgSelectModule } from  '@ng-select/ng-select';
import { ActivatedRoute, Router } from '@angular/router';
const plotTypes = require('src/app/shared/test/plot-types.json');
const metadata = require('src/app/shared/test/object-metadata.json');

fdescribe('PlotOptionsComponent', () => {

  const MockPlotService = {
    getPlotBuilder: () => new PlotBuilder(),
    getPlotTypes: () => of(plotTypes),
    getPlotType: () => null,
    setConfig: (name, length, callback: Function) => {
      const dimvars = metadata.dim_context;
      const datavars = metadata.typed_values;
      callback([
        new Dimension(dimvars[0], datavars),
        new Dimension(dimvars[1], datavars),
        new Dimension(dimvars[2], datavars)
      ]);
    }
  };

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
    spyOn(comp, 'ngOnInit').and.callThrough();
    spyOn(comp, 'getPlotTypes').and.callThrough();
    spectator.detectChanges();
    expect(comp.plotTypeData instanceof Array).toBeTruthy();
    expect(comp.plotTypeData).toHaveLength(6);
    expect(comp.plotTypeData[0]).toEqual(plotTypes.results[1]);
  });

  it('should add correct number of dimensions', () => {
    spectator.component.updatePlotType(plotTypes.results[1])

    const dimvars = metadata.dim_context;
    const datavars = metadata.typed_values;
    spectator.component.dimensions = [
       new Dimension(dimvars[0], datavars),
        new Dimension(dimvars[1], datavars),
        new Dimension(dimvars[2], datavars)
      ];
    spectator.detectChanges();
    expect(spectator.component.axisBlocks).not.toBeUndefined();
    expect(spectator.component.selectedPlotType).not.toBeUndefined();
    expect(spectator.queryAll('app-dimension-options')).toHaveLength(3);
  });
});
