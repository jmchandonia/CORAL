import { Component, OnInit, OnDestroy, Input, EventEmitter, Output } from '@angular/core';
import { DimensionRef, Dimension } from 'src/app/shared/models/plot-builder';
import { Subscription } from 'rxjs';
import { PlotService } from 'src/app/shared/services/plot.service';

@Component({
  selector: 'app-axis-labeler',
  templateUrl: './axis-labeler.component.html',
  styleUrls: ['./axis-labeler.component.css']
})
export class AxisLabelerComponent implements OnInit, OnDestroy {

  @Input() axis: string;
  @Input() dimension: Dimension;
  labelBuilderSub = new Subscription();
  labelBuilder: DimensionRef;
  labelArray: string[] = [];
  plotlyFormatString: string;
  displayOptions = false;

  constructor(private plotService: PlotService) { }

  ngOnInit() {
    this.labelBuilder = this.plotService.getLabelBuilder(this.axis);
    if (this.labelBuilder) {
      this.updateLabelArray(true);
    }
    this.labelBuilderSub = this.plotService.getUpdatedLabelBuilder()
      .subscribe(({axis, labelBuilder}) => {
        if (axis === this.axis) {
          this.labelBuilder = labelBuilder;
          this.updateLabelArray(true);
        }
      });
  }

  ngOnDestroy() {
    if (this.labelBuilderSub) {
      this.labelBuilderSub.unsubscribe();
    }
  }

  updateLabelArray(fromService: boolean) { // (change)="updateLabelArray(false) in html"
    if (!fromService) {
      this.labelBuilder.resetLabels();
      this.plotService.setLabelBuilder(this.labelBuilder, this.axis);
    }
    this.updatePlotlyFormatString();
  }

  updatePlotlyFormatString() {
      this.plotlyFormatString = this.labelBuilder.labels.join();
      this.submitFormatString();
  }

  submitFormatString() {
    // TODO: add format validation
    const split = this.plotlyFormatString.split(',');
    let idx = 0;
    this.labelBuilder.labels = [
      ...this.labelBuilder.dimVars.map((dimVar) => {
        if (dimVar.selected) {
          return split[idx++];
        } else {
          return '';
        }
      })
    ];
    this.plotService.updateFormatString(this.plotlyFormatString, this.axis);
  }

  get labelDisplay() {
    return this.labelBuilder.labels
      .map((label, idx) => {
        return label.replace(
          /#V[0-9]/gi,
          // TODO: escape markup so #V(n) badge can show up before or after user input
          // `<span class="badge badge-pill badge-primary">V${idx + 1}</span>`
          ''
          );
      });
  }

  toggleDisplayOptions() {
    this.displayOptions = !this.displayOptions;
  }

}
