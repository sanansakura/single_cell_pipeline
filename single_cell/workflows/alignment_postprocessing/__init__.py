'''
Created on Jul 11, 2017

@author: dgrewal
'''


'''
Created on Jul 6, 2017

@author: dgrewal
'''
import os
import pypeliner
import pypeliner.managed as mgd
import tasks

def create_bam_post_workflow(
    bam,
    bam_filename,
    bam_index_filename,
    ref_genome,
    metrics_summary_filename,
    gc_matrix_filename,
    sample_id,
    samplesheet,
    config,
    args, desc, 
    lanes):
 
    metrics_dir = os.path.join(args['out_dir'], 'metrics')
    markdups_metrics_filename = os.path.join(metrics_dir, 'markdups_metrics', '{}.markdups_metrics.txt'.format(sample_id))
    flagstat_metrics_filename = os.path.join(metrics_dir, 'flagstat_metrics', '{}.flagstat_metrics.txt'.format(sample_id))
    wgs_metrics_filename = os.path.join(metrics_dir, 'wgs_metrics', '{}.wgs_metrics.txt'.format(sample_id))
    gc_metrics_filename = os.path.join(metrics_dir, 'gc_metrics', '{}.gc_metrics.txt'.format(sample_id))
    gc_summary_filename = os.path.join(metrics_dir, 'gc_metrics', '{}.gc_metrics.summ.txt'.format(sample_id))
    gc_chart_filename = os.path.join(metrics_dir, 'gc_metrics', '{}.gc_metrics.pdf'.format(sample_id))
    insert_metrics_filename = os.path.join(metrics_dir, 'insert_metrics', '{}.insert_metrics.txt'.format(sample_id))
    insert_histogram_filename = os.path.join(metrics_dir, 'insert_metrics', '{}.insert_metrics.pdf'.format(sample_id))

    workflow = pypeliner.workflow.Workflow()

    workflow.setobj(
        obj=mgd.OutputChunks('lane'),
        value=lanes,
    )


    workflow.transform(
        name='bam_sort',
        ctx={'mem': config['high_mem']},
        func=tasks.bam_sort,
        args=(
            mgd.InputFile(bam),
            mgd.TempOutputFile('sorted.bam'),
            config
        ),
    )
   
    workflow.transform(
        name='bam_markdups',
        ctx={'mem': config['high_mem']},
        func=tasks.bam_markdups,
        args=(
            mgd.TempInputFile('sorted.bam'),
            mgd.OutputFile(bam_filename),
            mgd.OutputFile(markdups_metrics_filename),
            config
        ),
    )
   
    workflow.commandline(
        name='bam_index',
        ctx={'mem': config['low_mem']},
        args=(
            config['samtools'], 'index',
            mgd.InputFile(bam_filename),
            mgd.OutputFile(bam_index_filename),
        ),
    )
   
    workflow.commandline(
        name='bam_flagstat',
        ctx={'mem': config['low_mem']},
        args=(
            config['samtools'], 'flagstat',
            mgd.InputFile(bam_filename),
            '>',
            mgd.OutputFile(flagstat_metrics_filename),
        ),
    )
   
    workflow.transform(
        name='bam_collect_wgs_metrics',
        ctx={'mem': config['high_mem']},
        func=tasks.bam_collect_wgs_metrics,
        args=(
            mgd.InputFile(bam_filename),
            mgd.InputFile(ref_genome),
            mgd.OutputFile(wgs_metrics_filename),
            config,
        ),
    )
   
    workflow.transform(
        name='bam_collect_gc_metrics',
        ctx={'mem': config['high_mem']},
        func=tasks.bam_collect_gc_metrics,
        args=(
            mgd.InputFile(bam_filename),
            mgd.InputFile(ref_genome),
            mgd.OutputFile(gc_metrics_filename),
            mgd.OutputFile(gc_summary_filename),
            mgd.OutputFile(gc_chart_filename),
            config
        ),
    )
   
    workflow.transform(
        name='bam_collect_insert_metrics',
        ctx={'mem': config['high_mem']},
        func=tasks.bam_collect_insert_metrics,
        args=(
            mgd.InputFile(bam_filename),
            mgd.InputFile(flagstat_metrics_filename),
            mgd.OutputFile(insert_metrics_filename),
            mgd.OutputFile(insert_histogram_filename),
            config
        ),
    )
       
    workflow.transform(
        name='collect_metrics',
        ctx={'mem': config['low_mem']},
        func=tasks.collect_metrics,
        args=(
            mgd.InputFile(flagstat_metrics_filename),
            mgd.InputFile(markdups_metrics_filename),
            mgd.InputFile(insert_metrics_filename),
            mgd.InputFile(wgs_metrics_filename),
            mgd.InputFile(samplesheet),
            mgd.OutputFile(metrics_summary_filename),
            sample_id,
        ),
    )
   
    workflow.transform(
        name='collect_gc_metrics',
        ctx={'mem': config['low_mem']},
        func = tasks.collect_gc_metrics,
        args=(
            mgd.InputFile(gc_metrics_filename),
            mgd.OutputFile(gc_matrix_filename),
            ',',
            'NORMALIZED_COVERAGE',
            sample_id,
            'gcbias'
        ),
    )


    return workflow