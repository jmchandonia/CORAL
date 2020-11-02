import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { PlotService } from '../../shared/services/plot.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { PlotBuilder, Dimension } from '../../shared/models/plot-builder';
import { PlotlyConfig, AxisBlock } from 'src/app/shared/models/plotly-config';
import { CoreTypeAxis, CoreTypePlotBuilder } from 'src/app/shared/models/core-type-plot-builder';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { PlotlyBuilder, AxisOption, Axis } from 'src/app/shared/models/plotly-builder';
import { Response } from 'src/app/shared/models/response';
@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css'],
})
export class PlotOptionsComponent implements OnInit {

  public metadata: ObjectMetadata;
  public coreMetadata: CoreTypeAxis[];
  public allPlotTypeData: PlotlyConfig[];
  public plotTypeData: PlotlyConfig[]; // plotTypeData displayed depending on dimensionality
  public selectedPlotType: PlotlyConfig;
  public axisBlocks: AxisBlock[];
  public objectId: string;
  public previousUrl: string;
  public coreTypePlot = false;
  public numberOfAxes = 2; // currently just for core types
  private coreTypeName: string;
  public isMap = false; // determines if we should use UI for map config
  public mapBuilder: MapBuilder;
  public axisOptions: AxisOption[];
  public plot: PlotlyBuilder;
  public needsConstraints = false;
  public unableToPlot = false;

  constructor(
    private route: ActivatedRoute,
    private plotService: PlotService,
    private queryBuilder: QueryBuilderService,
    private router: Router,
    ) { }

  ngOnInit() {

    this.previousUrl = this.queryBuilder.getPreviousUrl();

    // get object id
    this.route.params.subscribe(params => {
        if (params['id']) {
          this.objectId = params.id;
          this.plot = this.plotService.getPlotlyBuilder();
          this.plot.objectId = params.id;
        }
    });

    this.route.queryParams.subscribe(queryParams => {
      if (queryParams['coreType']) {
        this.coreTypePlot = true;
        this.coreTypeName = queryParams['coreType'];
        const query = JSON.parse(localStorage.getItem('coreTypePlotParams'));
        this.plot = this.plotService.getPlotlyBuilder(true, query);
        this.plot.title = this.coreTypeName;
      }
    });

    if (this.coreTypePlot) {
      this.queryBuilder.getCoreTypeProps(this.coreTypeName)
        .subscribe((data: Response<AxisOption>) => {
          this.axisOptions = data.results;
          const query = JSON.parse(localStorage.getItem('coreTypePlotParams'));
          this.getPlotTypes();
        });
    } else {
      // get metadata and assign to AxisOption type 
      // TODO: needs to be formatted like this on the backend
      this.queryBuilder.getObjectMetadata(this.objectId)
        .subscribe((result: any) => {
        this.metadata = result; ///
        this.plot.title = this.metadata.data_type.oterm_name + ` (${this.objectId})`;
        this.axisOptions = [];
        result.dim_context.forEach((dim, i) => {
          dim.typed_values.forEach((dimVar, j) => {
            this.axisOptions.push({
              scalarType: dimVar.values.scalar_type,
              name: dimVar.value_no_units,
              displayName: dimVar.value_with_units,
              termId: dimVar.value_type.oterm_ref,
              dimension: i,
              dimensionVariable: j
            });
          });
        });
        result.typed_values.forEach(dataVar => {
          this.axisOptions.push({
            scalarType: dataVar.values.scalar_type,
            name: dataVar.value_no_units,
            displayName: dataVar.value_with_units,
            termId: dataVar.value_type.oterm_ref
          });
        });
        this.getPlotTypes();
      });
    }
    // this.getPlotTypes();
  }

  onNumberOfAxisChange(event) {
    if (this.numberOfAxes === 3) {
      this.plot.axes.z = new Axis();
    } else {
      delete this.plot.axes.z;
    }
    this.plotTypeData = this.allPlotTypeData.filter(val => {
      return val.n_dimensions === this.numberOfAxes - 1;
    })
  }

  getPlotTypes() { // TODO: add validation elements to plot-types.json
    // also TODO: add map types but figure out a way to only show it if theres lat and long
    this.plotService.getPlotTypes()
      .subscribe((data: Response<PlotlyConfig>) => {
        this.allPlotTypeData = data.results;
        this.plotTypeData = this.validateDimensions(data.results);
        if (this.plotTypeData.length === 0) {
          this.unableToPlot = true;
        }
    });
  }

  validateDimensions(plotTypes: PlotlyConfig[]) {
    // determine number of properties with numeric scalar in data to be plotted
    if (!this.coreTypePlot) {
      const totalLength = this.axisOptions.length;
      const totalNumericLength = this.axisOptions.reduce<number>((acc: number, axisOption: AxisOption) => {
        if ((this.isNumeric(axisOption.scalarType))) { return acc + 1; }
        return acc;
      }, 0);
      return plotTypes.filter(plotType => {
        if (plotType.n_dimensions > totalLength) { return false; }
        const totalNumericAxes = Object.entries(plotType.axis_data).reduce<number>((acc: number, [_, val]) => {
            if (val.numeric_only) { return acc + 1 }
            return acc;
        }, 0);
        if (totalNumericAxes > totalNumericLength) {
          return false;
        }
        return true;
      });
    }
  }

  isNumeric(scalar) {
    return scalar === 'int' || scalar === 'date' || scalar === 'float'
  }

  get coreTypesHaveLatAndLong() { // TODO: this should work for both core and dynamic types
    return Object.entries(this.coreMetadata)
      .filter(([key, val]) => val.name === 'latitude' || val.name === 'longitude')
      .length === 2;
  }

  get scalarCoreProperties() {
    return this.coreMetadata.filter(prop => {
      return prop.scalar_type === 'int' ||
        prop.scalar_type === 'float' ||
        prop.name === 'date'
    });
  }

  updatePlotType(event: PlotlyConfig) {
    this.isMap = false;
    if (event.map) {
      this.isMap = true;
      this.mapBuilder = new MapBuilder();
    } else {
      // TODO: this is redundant, can be viewed in this.plot.plotType
      this.plot.plotly_layout = event.plotly_layout;
      this.plot.plotly_trace = event.plotly_trace;
      this.axisBlocks = event.axis_blocks;
    }
    this.plot.plotType = event;
    // this.selectedPlotType = event; // TODO: this should just be in the plotybuilder models
  }

  submitPlot() {
    if (this.isMap) {
      localStorage.setItem('mapBuilder', JSON.stringify(this.mapBuilder));
      this.router.navigate(['/plot/map/result']);
      return;
    }

    localStorage.setItem('plotlyBuilder', JSON.stringify(this.plot));
    if (this.coreTypePlot) {
      this.router.navigate(['/plot/result'], {queryParams: {
        coreType: this.coreTypeName
      }});
    } else {
        this.router.navigate([`plot/result/${this.objectId}`]);
    } 
  }

  onGoBack(id) {
    const url = this.previousUrl ? this.previousUrl : `/search/result/brick/${id}`;
    this.router.navigate([url]);
  }

}
