import { async, ComponentFixture, TestBed } from '@angular/core/testing';
// import { AppModule } from 'src/app/app.module';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { PlotService } from  'src/app/shared/services/plot.service';
import { AxisLabelerComponent } from './axis-labeler.component';
import { Dimension } from 'src/app/shared/models/plot-builder';
import { Subject } from 'rxjs';
import { SafeHtmlPipe } from 'src/app/shared/pipes/safe-html.pipe';
const metadata = require('src/app/shared/test/object-metadata.json');


const dimension = new Dimension(metadata.dim_context, metadata.typed_values);
dimension.dimVars = metadata.dim_context[1].typed_values;
dimension.dimVars.forEach(dimVar => dimVar.selected = true);
dimension.label_pattern = 'Sequence Type=#V1, Sequence=#V2';
const dimVars = metadata.dim_context[1].typed_values;

describe('AxisLabelerComponent', () => {


  let spectator: Spectator<AxisLabelerComponent>;
  const createComponent = createComponentFactory({
    component: AxisLabelerComponent,
    imports: [
      FormsModule,
      HttpClientModule
    ],
    declarations: [
      SafeHtmlPipe
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimVars,
      dimension,
      labelPattern: 'Sequence Type=#V1, Sequence=#V2'
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should render all dimVars as checkboxes', () => {
    expect(spectator.queryAll('input.form-check-input.dim-var-option')).toHaveLength(2);
    expect(spectator.query('label.form-check-label')).toHaveText('Sequence Type');
  });

  it('should dynamically display label string as series of values', () => {
    expect(spectator.component.labelDisplay[0])
      .toEqual('<span>Sequence Type=<span class="badge badge-pill badge-primary">V1</span></span>');
  });

  it('should trigger updateSelectedLabels on check box click', () => {
    spyOn(spectator.component, 'updateSelectedLabels');
    spectator.click('input.form-check-input.dim-var-option');
    expect(spectator.component.updateSelectedLabels).toHaveBeenCalledWith(0);
  });

  it('should update label pattern on checkbox selection', () => {
    spectator.component.updateSelectedLabels(0);
    expect(spectator.component.dimension.label_pattern).toBe(' Sequence=#V2');
    expect(spectator.component.labelDisplay).toHaveLength(1);
  });

  it('should change label pattern UI correctly based on text input', () => {
    spectator.component.plotlyFormatString = 'abc=#V1, def=#V2';
    spectator.component.setLabels();
    expect(spectator.component.dimension.label_pattern).toBe('abc=#V1, def=#V2');
    expect(spectator.component.labelDisplay[0])
      .toEqual('<span>abc=<span class="badge badge-pill badge-primary">V1</span></span>');
  });
});
