import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit {

  brick: Brick;
  dimVars: DimensionVariable[] = [];
  testArray = [];
  mapped = false;
  loading = false;

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService
    ) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.brick.dimensions.forEach(dim => {
      this.dimVars = [...this.dimVars, ...dim.variables];
    });
  }

  testMap() {
    // this.uploadService.mapDimVarToCoreTypes(this.dimVars[0])
    //   .subscribe((result: any) => {
    //     console.log('RESULT', result);
    //   });
    this.loading = true;
    this.spinner.show();
    setTimeout(() => {
      this.testArray = this.dimVars.map(() => Math.floor(Math.random() * 3 ) + 1);
      this.dimVars.forEach((dimVar, idx) => {
        dimVar.totalCount = 100;
        switch(this.testArray[idx]) {
          case 1:
            dimVar.mappedCount = 100;
            break;
          case 2:
            dimVar.mappedCount = 95;
            break;
          case 3:
            dimVar.mappedCount = 0;
            break;
          default:
            dimVar.mappedCount = 0;
        }
        this.loading = false;
        this.spinner.hide();
        this.mapped = true;
      });
    }, 1000)
  }

  getMappedStatus(mapped, total) {
    if (mapped === total) {
      return 'status-column-success';
    }
    return mapped === 0 ? 'status-column-fail' : 'status-column-warn'
  }

}
